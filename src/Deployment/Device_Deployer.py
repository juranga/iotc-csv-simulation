# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import pandas as pd


class Device_Deployer(object):

    def __init__(self, azure_table_deployer, iot_central_deployer, key_vault_deployer):
        self.azure_table_deployer = azure_table_deployer
        self.iot_central_deployer = iot_central_deployer
        self.key_vault_deployer = key_vault_deployer
        self.device_models = []
        return

    # Creates the devices designated from the Simulated Devices csv file 
    def create_simulated_devices(self):
        from src.constants import SIM_DEVICES_PATH

        dataframe = pd.read_csv(SIM_DEVICES_PATH)
        id_count = 0
        for _, row in dataframe.iterrows():
            i = 0
            while i < int(row['NumberOfDevices']):
                model = row['DeviceModel']
                if not model in self.device_models:
                    self.device_models.append(model)
                device_id = 'simulateddevice' + str(id_count)
                entity = {
                    'PartitionKey': model,
                    'RowKey': row['DeviceType'],
                    'DeviceId': device_id,
                    'LastKnownRow': 1,
                    'SimulatedDataSource': row['SimulatedDataSource']
                }
                # Check if device deployment to central is successful 
                if self.iot_central_deployer.deploy_device(device_id= device_id, device_model= model):

                    # Retrieve Connection String 
                    connection_string = self.iot_central_deployer.get_device_connection_string(device_id)

                    # Insert Connection String in to Key Vault for Azure Function to Access
                    self.key_vault_deployer.insert_secret(device_id, connection_string)

                    # Insert a Device Entity for Azure Table to store state of device
                    self.azure_table_deployer.insert_device_entity(entity)
                    i += 1
                id_count +=1

    def get_device_models(self):
        return self.device_models