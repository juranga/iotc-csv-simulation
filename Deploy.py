# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azureml.core.authentication import InteractiveLoginAuthentication, fetch_tenantid_from_aad_token
from azure.mgmt.storage import StorageManagementClient
import os, sys

# Prevent local Pycache files from being stored 
sys.dont_write_bytecode = True 

from src.constants import CONFIG_PATH
from src.Deployment.ARM_Deployer import ARM_Deployer
from src.Deployment.Blob_Deployer import Blob_Deployer
from src.Deployment.Table_Deployer import Table_Deployer
from src.Common.Functions import load_json, write_to_config

################################################################################################
# Fill in values for customization & use in Deployment 
################################################################################################

# Subscription is obtained from azure portal. Ask management if you do not know which id to use.
subscription_id: str = '' if len(sys.argv) < 2 else sys.argv[1]

################################################################################################
# Deploy Azure Resources
################################################################################################
current_dir: str = os.getcwd()

# Load Config file to check if the deployment has already been ran.
config: dict = load_json(CONFIG_PATH)
deployed: bool = config['deployed']

# Get Default Parameters set by User 
default_param_path: str = os.path.join(current_dir, 'Templates', 'default.params.json')
default_params: dict = load_json(default_param_path)
location: str = default_params['location']['value']
resource_group: str = default_params['resourceGroupName']['value']

# Get Template dir by joining current dir and Templates folder
template_dir: str = os.path.join(current_dir, 'Templates')

# Authenticate for Azure Resource Deployment. Currently only supports Interactive Login
credentials = InteractiveLoginAuthentication(force=False, tenant_id=None)
central_url = 'https://apps.azureiotcentral.com'
IOT_AUTH_TOKEN = credentials._get_arm_token_using_interactive_auth(resource=central_url)

# Create Deployer class & deploy Azure Resources defined in the Templates Directory
arm_deployer = ARM_Deployer(credentials= credentials, subscription_id = subscription_id,
                              resource_group= resource_group, template_dir= template_dir,
                              location= location)


# Updates config file for two reasons:
# 1: Resources won't be provisioned twice
# 2: If new data models/csvs are added, running the script again deploys only these files.
if not deployed:
    arm_deployer.deploy_all()
    config['deployed'] = True
    write_to_config(config)
    

################################################################################################
# Deploy Blob CSV Files & Containers to Storage Account
################################################################################################

# Get Data Path Files & Storage Account Name
storage_account: str = config['storageAccountName']

csv_folder: str = os.path.join(current_dir, 'Data', 'DeviceData')
device_models_folder: str = os.path.join(current_dir, 'Data', 'DeviceModels')
device_csv_file: str = os.path.join(current_dir, 'Data')

# Obtain Storage Account credentials
storage_client = StorageManagementClient(credentials, subscription_id)
storage_keys = storage_client.storage_accounts.list_keys(resource_group, storage_account)
storage_keys: dict = {v.key_name: v.value for v in storage_keys.keys}

# Upload Device Data files in to 3 separate containers in Blob Storage
blob_deployer = Blob_Deployer(storage_account, storage_keys['key1'])
blob_deployer.upload_blobs_from_folder(folder=csv_folder, container_name='simcsvfiles')
blob_deployer.upload_blobs_from_folder(folder=device_models_folder, container_name='simdevicemodels')

################################################################################################
# Deploy Azure Table to Storage Account
# This is done to keep track of what row # the device is currently at in the csv simulated data 
# the device.
# TODO: Rethink Azure Table Deployment
################################################################################################

device_types_path: str = os.path.join(device_csv_file, 'SimulateDevices.csv')
table_deployer = Table_Deployer(storage_account, storage_keys['key1'], device_types_path)

# Create Devices table 
table_deployer.create_table(table_name='Devices')

# Deploy all Devices' Meta Data in to Table
table_deployer.create_device_entities()