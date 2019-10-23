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
    private string keyVaultUrl;
    private string blobContainerName;
    private Dictionary<string, Dictionary<string, string[]>> dataSources;
    private Microsoft.Azure.Storage.CloudStorageAccount blobStorageAccount;
    private Microsoft.WindowsAzure.Storage.CloudStorageAccount tableStorageAccount;
    private KeyVaultClient vaultClient;

    public CsvDeviceSimulator()
    {
        keyVaultUrl = Environment.GetEnvironmentVariable("KeyVaultBaseUrl");
        blobContainerName = "simcsvfiles";
        dataSources = new Dictionary<string, Dictionary<string, string[]>>();

        // Create KeyVault Client to fetch Connection String Secrets
        var tokenProvider = new AzureServiceTokenProvider();
        var authenticationCallback = new KeyVaultClient.AuthenticationCallback(tokenProvider.KeyVaultTokenCallback);
        vaultClient = new KeyVaultClient(authenticationCallback);
    }
    public async void SendTelemetryDataOfType(string deviceModel)
    {
        // Get Storage Connection Strings From Vault
        string storageConnectionString = getSecretFromVault("StorageAccountConnectionString");

        // Create Clients for blob storage & table storage accounts from storage connection string
        blobStorageAccount = Microsoft.Azure.Storage.CloudStorageAccount.Parse(storageConnectionString);
        tableStorageAccount = Microsoft.WindowsAzure.Storage.CloudStorageAccount.Parse(storageConnectionString);

        // Create Cloud Table Client to get the list of Devices of device model from Azure Table. 
        CloudTableClient tableClient = tableStorageAccount.CreateCloudTableClient();
        CloudTable table = tableClient.GetTableReference("devices");
        Console.WriteLine(table.ToString());

        // Create Query to get every device of specified Device Model
        var query = new TableQuery<SimulatedDeviceDetails>().Where(TableQuery.GenerateFilterCondition("PartitionKey",
                                                    QueryComparisons.Equal, deviceModel)
                                                    );

        TableContinuationToken continuationToken = default(TableContinuationToken);
        do
        {
            var tableQueryResult = table.ExecuteQuerySegmentedAsync(query, continuationToken).GetAwaiter().GetResult();
            foreach (var device in tableQueryResult.Results)
            {

                // If the csv file the device is reading from has not been loaded yet to dataSources dict, then we must load & store it.
                // This is done to cache the data sources so as to not continuously call Blob Storage and parse an entire csv file on each loop
                if (!dataSources.ContainsKey(device.SimulatedDataSource))
                {
                    string csvData = GetCSVBlobData(device.SimulatedDataSource);
                    string[] rows = csvData.Split('\n');
                    string[] properties = rows[0].Split(',');
                    Dictionary<string, string[]> tempCsvDict = new Dictionary<string, string[]>();
                    tempCsvDict.Add("rows", rows);
                    tempCsvDict.Add("columns", properties);
                    dataSources.Add(device.SimulatedDataSource, tempCsvDict);
                }

                Dictionary<string, string> payload = createPayload(device);
                SendPayloadToCentral(payload, device);
                updateDeviceAsync(device, table);
            }

            // Assign the new continuation token to tell the service where to
            // continue on the next iteration (or null if it has reached the end).
            continuationToken = tableQueryResult.ContinuationToken;

        } while (continuationToken != null);
    }
    private string GetCSVBlobData(string fileName)
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
    private string getSecretFromVault(string key)
    {
        var secret = vaultClient.GetSecretAsync(keyVaultUrl, key).GetAwaiter().GetResult();
        return secret.Value.ToString();
    }

    private Dictionary<string, string> createPayload(SimulatedDeviceDetails device)
    {

        // Split Comma Separated Values  
        string[] dataPoints = dataSources[device.SimulatedDataSource]["rows"][device.LastKnownRow].Split(',');
        string[] properties = dataSources[device.SimulatedDataSource]["columns"];

        // Create the Payload Dictionary
        Dictionary<String, String> payload = new Dictionary<string, string>();

        // Iterate through column ids of csv & map to current Device's telemetry
        for (int i = 0; i < properties.Length; i++)
        {
            payload.Add(properties[i], dataPoints[i]);
        }

        return payload;
    }

    private async void updateDeviceAsync(SimulatedDeviceDetails device, CloudTable table)
    {

        // Updating device requires replacing the entity in the table
        SimulatedDeviceDetails updatedDevice = new SimulatedDeviceDetails()
        {
            PartitionKey = device.PartitionKey,
            RowKey = device.RowKey,
            DeviceType = device.DeviceType,
            LastKnownRow = device.LastKnownRow + 1 == dataSources[device.SimulatedDataSource]["rows"].Length ? 1 : device.LastKnownRow + 1,
            SimulatedDataSource = device.SimulatedDataSource
        };

        // Update Table to set new last knownIndex for Device State
        TableOperation updateDeviceOperation = TableOperation.InsertOrReplace(updatedDevice);
        await table.ExecuteAsync(updateDeviceOperation);
    }

    private async void SendPayloadToCentral(Dictionary<string, string> payload, SimulatedDeviceDetails device)
    {
        string deviceConnectionString = getSecretFromVault(device.RowKey);

        using (var deviceClient = DeviceClient.CreateFromConnectionString(deviceConnectionString, TransportType.Mqtt))
        {
            // Convert Payload Dictionary to Json Object
            var messageString = JsonConvert.SerializeObject(payload);

            // Serialize object to expected Device Message
            var deviceMessage = new Message(Encoding.UTF8.GetBytes(messageString));

            // Send Message to IoT Hub
            deviceClient.SendEventAsync(deviceMessage, new CancellationToken()).Wait();
        }
    }

    public class SimulatedDeviceDetails : TableEntity
    {

        public string DeviceType { get; set; }

        public string SimulatedDataSource { get; set; }

        public int LastKnownRow { get; set; }
    }
}