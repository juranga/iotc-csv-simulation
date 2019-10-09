# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.storage.table import TableService
import os
import pandas as pd

class Table_Deployer(object):

    def __init__(self, name: str, key: str, simulated_devices_csvpath: str):
        self.storage_acct_name: str = name
        self.storage_key: str = key
        self.client = TableService(account_name= name, account_key=key)
        self.table_name: str = 'devices'
        self.simulated_devices_csvpath = simulated_devices_csvpath
        
    def create_table(self, table_name='devices'):
        if self.client.exists(self.table_name):
            return
        self.client.create_table(self.table_name)

    def insert_device_entity(self, entity: dict):
        self.client.insert_entity(self.table_name, entity)