# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import pandas as pd


class Device_Deployer(object):

    def __init__(self, azure_table_deployer, iot_central_deployer, azure_function_deployer):
        self.azure_table_deployer = azure_table_deployer
        self.iot_central_deployer = iot_central_deployer
        self.azure_function_deployer = azure_function_deployer
        self.iot_hub = None
        self.sas = None
        return

    # Creates the devices designated from the Simulated Devices csv file 
    def create_simulated_devices(self):
        from src.constants import SIM_DEVICES_PATH

        dataframe = pd.read_csv(SIM_DEVICES_PATH)
        id_count = 0
        for _, row in dataframe.iterrows():
            for n in range(0, int(row['NumberOfDevices'])):
                device_id = 'simulateddevice' + str(id_count)
                entity = {
                    'PartitionKey': device_id,
                    'RowKey': row['DeviceType'],
                    'LastKnownRow': 0,
                    'SimulatedDataSource': row['SimulatedDataSource']
                }
                # Check if device deployment to central is successful 
                if self.iot_central_deployer.deploy_device(device_id= device_id, device_model= row['DeviceModel']):

                    # Retrieve Connection String to parse for hub and sas token
                    # This will be used by the Azure Function to send telemetry functioning as that device
                    connection_string = self.iot_central_deployer.get_device_connection_string(device_id)

                    # Update Azure Function App Settings to include the IoT Hub & the Sas Key.
                    # This is done so that the Azure Function can easily obtain the necessary
                    # authentication to send telemetry as a device.
                    if self.iot_hub == None and not connection_string == None:
                        connection_string = connection_string.split(';')
                        self.iot_hub = connection_string[0] #iothub
                        self.sas = connection_string[2] #sas token
                        device_settings = {
                            "iotHub": self.iot_hub,
                            "sas": self.sas
                        }
                        self.azure_function_deployer.insert_app_settings(settings=device_settings)

                    # Insert a Device Entity for Azure Table to store state of device
                    self.azure_table_deployer.insert_device_entity(entity)
                    id_count += 1