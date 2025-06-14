# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.storage.blob import BlockBlobService
import os

class Blob_Deployer(object):

    def __init__(self, name: str, key: str):
        self.storage_acct_name: str  = name
        self.storage_key: str = key
        self.blob_client = BlockBlobService(account_name=name, account_key=key)

    # Create Azure Blob Service & CSV File containers
    def upload_blobs_from_folder(self, folder, container_name='devicedata'):
        container = self.blob_client.create_container(container_name)
        if container:
            print('Container {} has been created'.format(container_name))
        else:
            print('Container {} already exists.'.format(container_name))
        print('Uploading data files...')

        for file_name in os.listdir(folder):
            file_path: str = os.path.join(folder, file_name)
            self.blob_client.create_blob_from_path(
                container_name=container_name, blob_name=file_name, file_path=file_path)