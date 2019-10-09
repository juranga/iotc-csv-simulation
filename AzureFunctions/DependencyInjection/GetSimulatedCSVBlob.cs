// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Microsoft.Azure.Storage.CloudStorageAccount;
using Microsoft.Azure.WebJobs;
using Microsoft.Extensions.Logging;
using Microsoft.WindowsAzure.Storage.Blob;
using DynamicDictionary;

namespace Microsoft.Azure.IotCentral.Simulation
{

    public class CSVBus {

        public CSVBus() {
            
        }
        
        
        public void ListBlobsInContainer(string containerName, string file_name)
            {
                var storageAccount = CloudStorageAccount.Parse(this.blobConnectionString);
                var cloudBlobContainer = storageAccount.CreateCloudBlobClient().GetContainerReference(containerName);
                if (cloudBlobContainer.Exists())
                {
                    var results = cloudBlobContainer.ListBlobs(prefix:"");
                    foreach (IListBlobItem item in results)
                    {
                        Console.WriteLine(item.Uri);
                    }
                }
            }

        public void GetBlobInContainer(string containerName, string file_name) {
            var storageAccount = CloudStorageAccount.Parse(Environment.GetEnvironmentVariable("AzureStorageConnectionString", EnvironmentVariableTarget.Process));
            CloudBlobClient blobClient = storageAccount.CreateCloudBlobClient(containerName);
            
        }
    }
}