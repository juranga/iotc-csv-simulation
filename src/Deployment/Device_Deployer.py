# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import pandas as pd

from src.Deployment.Table_Deployer import Table_Deployer
from src.Deployment.Iot_Central_Deployer import Iot_Central_Deployer

class Device_Deployer(object):

    def __init__(self, table_deployer, iotcentral_deployer):
        self.table_deployer = table_deployer
        self.iotcentral_deployer = iotcentral_deployer
        return

    def create_simulated_devices(self):
        dataframe = pd.read_csv(self.table_deployer.device_type_path)
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
                if self.iotcentral_deployer.deploy_device(device_id= device_id, device_model= row['DeviceModel']):
                    self.table_deployer.client.insert_entity(self.table_deployer.table_name, entity)
                    id_count += 1