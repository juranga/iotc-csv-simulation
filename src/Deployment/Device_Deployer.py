# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import pandas as pd
import uuid, sys


class Device_Deployer(object):

    def __init__(self, azure_table_deployer, iot_central_deployer, key_vault_deployer):
        self.azure_table_deployer = azure_table_deployer
        self.iot_central_deployer = iot_central_deployer
        self.key_vault_deployer = key_vault_deployer
        self.device_models = []
        return

    # Creates the devices designated from the Simulated Devices csv file  & Deploys them to Resources
    def deploy_simulated_devices(self, sim_devices_csv: str):

        dataframe = pd.read_csv(sim_devices_csv)
        for _, row in dataframe.iterrows():
            i = 0
            break_retry = 1
            while i < int(row['NumberOfDevices']):
                model = row['DeviceModel']
                if not model in self.device_models:
                    self.device_models.append(model)
                first_half = str(uuid.uuid4().fields[-1])[:5]
                second_half = str(uuid.uuid4().fields[-1])[:5]
                device_id = 'device'+first_half+second_half
                entity = {
                    'PartitionKey': model,
                    'RowKey': row['DeviceType'],
                    'DeviceId': device_id,
                    'LastKnownRow': 1,
                    'SimulatedDataSource': row['SimulatedDataSource']
                }
                # Check if device deployment to central is successful 
                if self.iot_central_deployer.create_device(device_id= device_id, device_model= model):

                    # Retrieve Connection String 
                    connection_string = self.iot_central_deployer.get_device_connection_string(device_id)

                    # Insert Connection String in to Key Vault for Azure Function to Access
                    self.key_vault_deployer.insert_secret(device_id, connection_string)

                    # Insert a Device Entity for Azure Table to store state of device
                    self.azure_table_deployer.insert_device_entity(entity)
                    i += 1
                else:
                    break_retry += 1
                    if break_retry == 3:
                        print('Something is wrong with Device Creation right now.. Please try deploying later.')
                        sys.exit()

    def get_device_models(self):
        return self.device_models