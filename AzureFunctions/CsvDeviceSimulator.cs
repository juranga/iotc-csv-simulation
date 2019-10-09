using System;
using System.IO;
using System.Threading;
using Microsoft.Azure.Storage.Blob;
using Microsoft.WindowsAzure.Storage.Table;
using System.Collections.Generic;
using System.Linq;

namespace ConsoleApp1
{
    public class CsvDeviceSimulator
    {
        private string blobContainerName;
        private Dictionary<String, String> dataSources;
        private Microsoft.Azure.Storage.CloudStorageAccount blobStorageAccount;
        private Microsoft.WindowsAzure.Storage.CloudStorageAccount tableStorageAccount;

        public CsvDeviceSimulator()
        {
            dataSources = new Dictionary<string, string>();
            blobContainerName = "simcsvfiles";
            // blobStorageAccount = Microsoft.Azure.Storage.CloudStorageAccount.Parse(Environment.GetEnvironmentVariable("AzureStorageConnectionString", EnvironmentVariableTarget.Process));
            // tableStorageAccount = Microsoft.Azure.Storage.CloudStorageAccount.Parse(Environment.GetEnvironmentVariable("AzureStorageConnectionString", EnvironmentVariableTarget.Process));
            blobStorageAccount = Microsoft.Azure.Storage.CloudStorageAccount.Parse(access_key);
            tableStorageAccount = Microsoft.WindowsAzure.Storage.CloudStorageAccount.Parse(access_key);
        }

        public async void SendTelemetryData(string deviceType)
        {
            CloudTableClient tableClient = tableStorageAccount.CreateCloudTableClient();
            CloudTable table = tableClient.GetTableReference("devices");
            TableQuery query= new TableQuery().Where(TableQuery.GenerateFilterCondition("PartitionKey",
                                                     QueryComparisons.Equal, deviceType)
                                                     );

            var continuationToken = default(TableContinuationToken);
            do
            {
                var tableQueryResult = await table.ExecuteQuerySegmentedAsync(query, continuationToken);
                foreach (var device in tableQueryResult.Results) {

                    // If Simulated Data Source has not been loaded yet to dataSources dict, then load it & store it.
                    // This is done to cache the data sources & not continuously parse an entire csv file for devices
                    // that use the same csv file as a data source.
                    if (!dataSources.ContainsKey(device.SimulatedDataSource))
                    {
                        dataSources.Add(device.SimulatedDataSource, GetCSVBlobData(device.SimulatedDataSource));
                    }

                    // Get the Device's Last Known State.
                    int lastKnownIndex = Int32.Parse(device.LastKnownRow);
                    string csvData = dataSources[device.SimulatedDataSource];
                    string[] row = csvData.Split('\n');
                    string[] dataPoints = row[lastKnownIndex].Split(',');
                    // TODO: don't forget to remove white spaces in text here to send correct telemetry

                    // TODO: Get the Device Secret from KeyVault

                
                    // TODO: Send the Device's Telemetry to IoT Central

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

        public static void Main(string[] args)
        {
            CsvDeviceSimulator bdr = new CsvDeviceSimulator();
            string fileName = "RepeatingDailyPVEnergyGenerationCsv.csv";

            string csvData = bdr.GetCSVBlobData(fileName);
            string[] row = csvData.Split('\n');
            string[] dataPoints = row[0].Split(',');
            Console.WriteLine(row[0]);
            Thread.Sleep(1000000);
        }
    }
}
