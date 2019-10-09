from azure.keyvault.secrets import SecretClient


class Keyvault_Deployer(object):

    def __init__(self, credentials, subscription_id: str, resource_group: str, keyvault_name: str):
        self.keyvault_url: str = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.KeyVault/vaults/{}'.format(subscription_id, resource_group, keyvault_name)
        self.secret_client = SecretClient(vault_url = self.keyvault_url, credential= credentials)

    def insert_secret(self, name, value):
        self.secret_client.set_secret(name, value)
