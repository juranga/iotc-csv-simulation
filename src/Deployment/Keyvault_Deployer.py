# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.keyvault.secrets import SecretClient
from azureml.core.authentication import InteractiveLoginAuthentication
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient
import requests

class Keyvault_Deployer(object):

    def __init__(self, credentials, subscription_id: str, resource_group: str, keyvault_name: str):
        client_id = 'https://vault.azure.net'
        auth = credentials._get_arm_token_using_interactive_auth(resource=client_id)
        self.header = {
            'Authorization': 'Bearer ' + auth
        }
        self.client = KeyVaultManagementClient(credentials, subscription_id)
        self.vault = self.client.vaults.get(resource_group, keyvault_name)

    def insert_secret(self, name:str, value:str):
        url = '{}/secrets/{}?api-version=7.0'.format(self.vault.properties.vault_uri, name)
        body = {
            'value': value
        }
        resp = requests.put(url, headers=self.header, json=body)
        if not resp.status_code == 200:
            print('Failed to add secret to Keyvault')
            print('Error message: {}'.format(resp.content))
