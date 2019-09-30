from azureml.core.authentication import InteractiveLoginAuthentication, fetch_tenantid_from_aad_token
from azure.mgmt.storage import StorageManagementClient
import os, sys

# Prevent local Pycache files from being stored 
sys.dont_write_bytecode = True 

from src.Deployment.ARM_Deployer import ARM_Deployer
from src.Deployment.Blob_Deployer import Blob_Deployer
from src.Common.Functions import load_json, write_json

################################################################################################
# Fill in values for customization & use in Deployment 
################################################################################################
# Subscription is obtained from azure portal. Ask management if you do not know which to use.
subscription_id: str = '' if len(sys.argv) < 2 else sys.argv[1]

################################################################################################
# Deploy Azure Resources
################################################################################################
current_dir = os.getcwd()

# Load Config file to check if the deployment has already been ran.
config_file = 'config.json'
config = load_json(config_file)
deployed = config['deployed']

# Get Default Param Path for Storage Account Name & Location
default_param_path: str = os.path.join(current_dir, 'Templates', 'default.params.json')
default_params = load_json(default_param_path)
location: str = default_params['location']['value']

# Get Template dir by joining current dir and Templates folder
template_dir: str = os.path.join(current_dir, 'Templates')

# Deployment Name & Resource Group Name
resource_group: str = 'iotcustomsimulation'

# Authenticate for Azure Resource Deployment. Currently only supports Interactive Login
credentials = InteractiveLoginAuthentication(force=False, tenant_id=None)

# Create Deployer class & deploy Azure Resources defined in the Templates Directory
arm_deployer = ARM_Deployer(credentials= credentials, subscription_id = subscription_id,
                              resource_group= resource_group, template_dir= template_dir,
                              location=location)
if not deployed:
    arm_deployer.deploy_all()
    config['deployed'] = True
    write_json(config_file, data=config)
    

################################################################################################
# Deploy Blob Files & Containers corresponding to JSON to Storage Account
################################################################################################

# Get Data Path Files & Storage Account Name
storage_account: str = default_params['storageAccountName']['value']

csv_folder: str = os.path.join(current_dir, 'Data', 'DeviceDataCSVs')
device_types_folder: str = os.path.join(current_dir, 'Data', 'DeviceTypes')

# Obtain Storage Account credentials
storage_client = StorageManagementClient(credentials, subscription_id)
storage_keys = storage_client.storage_accounts.list_keys(resource_group, storage_account)
storage_keys: dict = {v.key_name: v.value for v in storage_keys.keys}

# Upload Device Data files in to 3 separate containers in Blob Storage
blob_deployer = Blob_Deployer(storage_account, storage_keys['key1'])
blob_deployer.upload_blobs_from_folder(folder=csv_folder, container_name='csvfiles')
blob_deployer.upload_blobs_from_folder(folder=device_types_folder, container_name='devicedefinitionfiles')