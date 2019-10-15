using System;
using System.IO;
using System.Threading;
using Microsoft.Azure.Storage.Blob;
using Microsoft.Azure.KeyVault;
using Microsoft.Azure.Services.AppAuthentication;
using Microsoft.WindowsAzure.Storage.Table;
using Microsoft.Azure.Devices.Client;
using System.Collections.Generic;
using Newtonsoft.Json;
using System.Text;

public class CsvDeviceSimulator
{
    private string storageAccountName;
    private string keyVaultUrl;
    private Dictionary<String, String> dataSources;
    private string blobContainerName;
    private Microsoft.Azure.Storage.CloudStorageAccount blobStorageAccount;
    private Microsoft.WindowsAzure.Storage.CloudStorageAccount tableStorageAccount;

    public CsvDeviceSimulator()
    {
        storageAccountName = Environment.GetEnvironmentVariable("StorageAccountName");
        keyVaultUrl = Environment.GetEnvironmentVariable("KeyVaultBaseUrl");
        dataSources = new Dictionary<string, string>();
        blobContainerName = "simcsvfiles";
    }

    public async void SendTelemetryDataOfType(string deviceModel)
    {
        // Create KeyVault Client to fetch Connection String Secrets
        var tokenProvider = new AzureServiceTokenProvider();
        var authenticationCallback = new KeyVaultClient.AuthenticationCallback(tokenProvider.KeyVaultTokenCallback);
        KeyVaultClient vaultClient = new KeyVaultClient(authenticationCallback);

        // Create Clients for blob storage & table storage accounts from storage connection string
        var AzureStorageSecret = await vaultClient.GetSecretAsync(keyVaultUrl, "StorageAccountConnectionString");
        string storageConnectionString = AzureStorageSecret.Value;
        blobStorageAccount = Microsoft.Azure.Storage.CloudStorageAccount.Parse(storageConnectionString);
        tableStorageAccount = Microsoft.WindowsAzure.Storage.CloudStorageAccount.Parse(storageConnectionString);

        // Create Cloud Table Client to get the list of Devices of device model from Azure Table. 
        CloudTableClient tableClient = tableStorageAccount.CreateCloudTableClient();
        CloudTable table = tableClient.GetTableReference("devices");
        var query = new TableQuery<SimulatedDeviceDetails>().Where(TableQuery.GenerateFilterCondition("PartitionKey",
                                                    QueryComparisons.Equal, deviceModel)
                                                    );

        var continuationToken = default(TableContinuationToken);
        do
        {
            var tableQueryResult = await table.ExecuteQuerySegmentedAsync(query, continuationToken);

            foreach (var device in tableQueryResult.Results)
            {

                // If Simulated Data Source has not been loaded yet to dataSources dict, then load it & store it.
                // This is done to cache the data sources so as to not continuously parse an entire csv file for each device
                // that use the same csv file as a data source.
                if (!dataSources.ContainsKey(device.SimulatedDataSource))
                {
                    dataSources.Add(device.SimulatedDataSource, GetCSVBlobData(device.SimulatedDataSource));
                }

                // Get Device id
                string deviceId = "DeviceId=" + device.RowKey;

                // Get the Device's Last Known State.
                int lastKnownIndex = Int32.Parse(device.LastKnownRow);
                string csvData = dataSources[device.SimulatedDataSource];
                string[] rows = csvData.Split('\n');
                string[] properties = rows[0].Split(',');
                string[] dataPoints = rows[lastKnownIndex].Split(',');

                // Create the Payload Dictionary
                Dictionary<String, String> payload = new Dictionary<string, string>();

                // Iterate through column ids (properties) of csv 
                // & map to current Device's telemetry at last known index.
                for (int i = 0; i < properties.Length; i++)
                {
                    payload.Add(properties[i], dataPoints[i]);
                }

                // Get Device Connection String from Keyvault
                var DeviceConnectionSecret = await vaultClient.GetSecretAsync(keyVaultUrl, device.RowKey);
                string deviceConnectionString = DeviceConnectionSecret.Value;

                // Send the Device's Telemetry to IoT Central
                using (var deviceClient = DeviceClient.CreateFromConnectionString(deviceConnectionString, TransportType.Mqtt))
                {
                    // Convert Payload Dictionary to Json Object
                    var messageString = JsonConvert.SerializeObject(payload);

                    // Serialize object to expected Device Message
                    var deviceMessage = new Message(Encoding.UTF8.GetBytes(messageString));

                    // Send Message to IoT Hub
                    deviceClient.SendEventAsync(deviceMessage, new CancellationToken()).Wait();
                }

                // Update Device's Last Known Index.
                // If end of CSV file has been reached, reset to starting position.
                lastKnownIndex = lastKnownIndex + 1 == rows.Length ? 1 : lastKnownIndex + 1;

                SimulatedDeviceDetails updatedDevice = new SimulatedDeviceDetails()
                {
                    PartitionKey = device.PartitionKey,
                    RowKey = device.RowKey,
                    LastKnownRow = lastKnownIndex.ToString(),
                    SimulatedDataSource = device.SimulatedDataSource
                };

                // Update Table to set new last knownIndex for Device State
                TableOperation updateDevice = TableOperation.InsertOrReplace(updatedDevice);
                await table.ExecuteAsync(updateDevice);
            }

            // Assign the new continuation token to tell the service where to
            // continue on the next iteration (or null if it has reached the end).
            continuationToken = tableQueryResult.ContinuationToken;

        } while (continuationToken != null);

    }
    public string GetCSVBlobData(string fileName)
    {
        CloudBlobClient blobClient = blobStorageAccount.CreateCloudBlobClient();
        CloudBlobContainer container = blobClient.GetContainerReference(blobContainerName);
        CloudBlockBlob blockBlobReference = container.GetBlockBlobReference(fileName);
        string text;

        using (var memoryStream = new MemoryStream())
        {
            blockBlobReference.DownloadToStream(memoryStream);

            text = System.Text.Encoding.UTF8.GetString(memoryStream.ToArray());
        }

        return text;
    }

    public class SimulatedDeviceDetails : TableEntity
    {
        public new string PartitionKey { get; set; }

        public new string RowKey { get; set; }

        public string SimulatedDataSource { get; set; }

        public string LastKnownRow { get; set; }
    }
}