// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Microsoft.Azure.WebJobs;
using Microsoft.Extensions.Logging;
using Microsoft.WindowsAzure.Storage.Blob;

namespace Microsoft.Azure.IotCentral.Simulation
{

    public class EnergyTelemetry {
        
    }
    public class SimulatedEnergyTelemetryBridgeTrigger
    {
        private readonly dynamic device;
        private string jsonModel;

        [FunctionName("SimulatedEnergyTelemetryBridgeTrigger")]
        public Task Run([TimerTrigger("0 * * * * *")]TimerInfo timer, ILogger log, CloudBlockBlob energyDeviceModel, CancellationToken cancellationToken)
        {
            this.jsonModel = BeginDownloadText();
            this.device = JsonConvert.DeserializeObject(this.jsonModel);
        }
    }
}

