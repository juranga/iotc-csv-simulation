// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.WebJobs;
using Microsoft.Extensions.Logging;

namespace Microsoft.Azure.IotCentral.Simulation
{
    public class SimulatedEnergyTelemetryBridgeTrigger
    {
        private readonly Bridge<SimulatedEnergyTelemetry> _bridge;

        public SimulatedEnergyTelemetryBridgeTrigger(Bridge<SimulatedEnergyTelemetry> bridge)
        {
            _bridge = bridge ?? throw new ArgumentNullException(nameof(bridge));
        }

        [FunctionName("SimulatedEnergyTelemetryBridgeTrigger")]
        public Task Run([TimerTrigger("0 * * * * *")]TimerInfo timer, ILogger log, CancellationToken cancellationToken)
        {
            return _bridge.RunAsync(cancellationToken);
        }
    }
}

