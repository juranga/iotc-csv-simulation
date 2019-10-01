# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.storage.table import TableService
import os
import pandas as pd

class Table_Deployer(object):

    def __init__(self, name: str, key: str, device_type_path: str):
        self.storage_acct_name: str = name
        self.storage_key: str = key
        self.client = TableService(account_name= name, account_key=key)
        self.table_name: str = 'devices'
        self.device_type_path = device_type_path
        
    def create_table(self, table_name: str = 'devices'):
        self.table_name = table_name
        if self.client.exists(self.table_name):
            return
        self.client.create_table(self.table_name)

    def create_device_entities(self):
        dataframe = pd.read_csv(self.device_type_path)
        for _, row in dataframe.iterrows():
            entity = {
                'PartitionKey': row['DeviceType'],
                'RowKey': row['IOTC_DeviceID'],
                'NextRow': 0,
                'SimulatedDataSource': row['SimulatedDataSource']
            }
            self.client.insert_entity(self.table_name, entity)