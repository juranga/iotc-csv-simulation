# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import pandas as pd

class Device_Deployer(object):

    def __init__(self, azure_table_deployer, iot_central_deployer, keyvault_deployer):
        self.azure_table_deployer = azure_table_deployer
        self.iot_central_deployer = iot_central_deployer
        self.keyvault_deployer = keyvault_deployer
        return

    # Creates the devices designated from the Simulated Devices csv file 
    def create_simulated_devices(self):
        dataframe = pd.read_csv(self.azure_table_deployer.simulated_devices_csvpath)
        id_count = 0
        for _, row in dataframe.iterrows():
            for n in range(0, int(row['NumberOfDevices'])):
                device_id = 'simulateddevice' + str(id_count)
                entity = {
                    'PartitionKey': device_id,
                    'RowKey': row['DeviceType'],
                    'NextRow': 0,
                    'SimulatedDataSource': row['SimulatedDataSource']
                }
                # Check if device deployment to central is successful 
                if self.iot_central_deployer.deploy_device(device_id= device_id, device_model= row['DeviceModel']):

                    # Retrieve Connection String & insert in to Keyvault
                    # This will be used by the Azure Function to send telemetry functioning as that device
                    connection_string = self.iot_central_deployer.get_device_connection_string(device_id)
                    self.keyvault_deployer.insert_secret(name=device_id, value=connection_string)

                    # Insert a Device Entity for Azure Table to store state of device
                    self.azure_table_deployer.insert_device_entity(entity)
                    id_count += 1