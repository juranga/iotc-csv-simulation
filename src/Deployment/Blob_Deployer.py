from azure.storage.blob import BlockBlobService

class Blob_Deployer(object):

    def __init__(name: str, key: str):
        self.storage_acct_name = name
        self.storage_key = key
        self.blob_client = BlockBlobService(
            account_name=self.storage_acct_name, account_key=self.storage_key)

    # Create Azure Blob Service & CSV Files container
    def upload_blobs_from_folder(folder, container_name='datafiles'):
        container = self.blob_client.create_container(container_name)
        if container:
            print('Container {} has been created'.format(container_name))
        else:
            print('Container {} already exists.'.format(container_name))
        print('Uploading data files...')

        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            self.blob_client.create_blob_from_path(
                container_name=container_name, blob_name=file_name, file_path=file_path)