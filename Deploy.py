# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azureml.core.authentication import InteractiveLoginAuthentication, fetch_tenantid_from_aad_token
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.storage import StorageManagementClient
import os, sys, shutil

# Prevent local Pycache files from being stored 
sys.dont_write_bytecode = True 

from src.constants import CONFIG_PATH
from src.Deployment.ARM_Deployer import ARM_Deployer
from src.Deployment.Blob_Deployer import Blob_Deployer
from src.Deployment.Table_Deployer import Table_Deployer
from src.Deployment.Device_Deployer import Device_Deployer
from src.Deployment.Iot_Central_Deployer import Iot_Central_Deployer
from src.Deployment.Azure_Function_Deployer import Azure_Function_Deployer
from src.Deployment.Keyvault_Deployer import Keyvault_Deployer
from src.Common.Functions import load_json, write_to_config

################################################################################################
# Fill in value in this section for Subscription Id
################################################################################################

# Subscription is obtained from azure portal. Ask management if you do not know which id to use.
subscription_id: str = '' if len(sys.argv) < 2 else sys.argv[1]

################################################################################################
# Obtain Credentials via Interactive Login & Deploy Azure Resources
################################################################################################

current_dir: str = os.getcwd()

# Load Config file to check if the deployment has already been ran.
config: dict = load_json(CONFIG_PATH)
has_ARM_deployed: bool = config['deployed']

# Get Default Parameters set by user
default_param_path: str = os.path.join(current_dir, 'Templates', 'default.params.json')
default_params: dict = load_json(default_param_path)
location: str = default_params['location']['value']
resource_group: str = default_params['resourceGroupName']['value']

# Ugly way to get IoT Central App Name and Keyvault Name.
# Getting this info currently is hard coded and error prone. 
# These problems would be easy to fix with a UI.. TODO Potentially Rethink Config State
iot_app_name: str = default_params['0']['subdomain']['value']

# Get Template dir by joining current dir and Templates folder
template_dir: str = os.path.join(current_dir, 'Templates')

# Authenticate for Azure Resource Deployment 
credentials = InteractiveLoginAuthentication(force=False, tenant_id=None)

# Create Deployer class for ARM resources
arm_deployer = ARM_Deployer(credentials= credentials, subscription_id = subscription_id,
                            resource_group= resource_group, template_dir= template_dir,
                            location= location)


# Deploy Azure Resources & Update config file.
# Config file is updated for two reasons: 
# 1: Resources won't be provisioned twice
# 2: If new data models/csvs are added, running the script again deploys only these files.
if not has_ARM_deployed:
    arm_deployer.deploy_all()
    config['deployed'] = True
    write_to_config(config)

# Reload config to obtain keyvault & Azure Function state
config = load_json(CONFIG_PATH)
keyvault_name = config['keyvault']
azfn_name = config['azfn']

################################################################################################
# Obtain Storage Account Credentials & Deploy Blob CSV Files, Containers, & Azure Table
# Azure Table is used for storing Device State
################################################################################################

# Get Data Path Files & Storage Account Name
config = load_json(CONFIG_PATH) # Reload Config to get storageAccountName
storage_account: str = config['storageAccountName']

# Get Folder Paths for Simulated CSVs & Device Models
csv_folder: str = os.path.join(current_dir, 'Data', 'DeviceData')
device_models_folder: str = os.path.join(current_dir, 'Data', 'DeviceModels')

# Obtain Storage Account credentials
storage_client = StorageManagementClient(credentials, subscription_id)
storage_keys = storage_client.storage_accounts.list_keys(resource_group, storage_account)
storage_keys: dict = {v.key_name: v.value for v in storage_keys.keys}

# Upload Device Data files in to 3 separate containers in Blob Storage
blob_deployer = Blob_Deployer(storage_account, storage_keys['key1'])
blob_deployer.upload_blobs_from_folder(folder=csv_folder, container_name='simcsvfiles')
blob_deployer.upload_blobs_from_folder(folder=device_models_folder, container_name='simdevicemodels')

# Create Azure Table via Table Deployer Class
table_deployer = Table_Deployer(name=storage_account, key=storage_keys['key1'])
table_deployer.create_table(table_name='devices')


################################################################################################
# Deploy Devices to IoT Central, Device state to Azure Table, and Device Connection Strings
# To Azure KeyVault.
# Connection strings are needed for Azure Function to authenticate as device & send telemetry.
################################################################################################

# Create Keyvault and IoT Central Deployers 
central_deployer = Iot_Central_Deployer(credentials, app_domain_name=iot_app_name)
key_vault_deployer = Keyvault_Deployer(credentials, subscription_id, resource_group, keyvault_name)

# Insert Storage Connection string to Keyvault, as Azure Function requires it.
storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName={};AccountKey={};EndpointSuffix=core.windows.net'.format(storage_account, storage_keys['key1'])
key_vault_deployer.insert_secret('StorageAccountConnectionString', storage_connection_string)

# Deploy Models in DeviceModels folder
central_deployer.deploy_models(models_dir=device_models_folder)

# Create Deployer class for Devices & Create simulated Devices in Central
simulate_devices_path = os.path.join(current_dir, 'Data', 'SimulateDevices.csv')
device_deployer = Device_Deployer(azure_table_deployer=table_deployer, iot_central_deployer=central_deployer, key_vault_deployer=key_vault_deployer)
device_deployer.deploy_simulated_devices(simulate_devices_path)

################################################################################################
# Final Step: Create & Upload the Azure Functions to the specified resource group that will
# simulate all devices
################################################################################################

device_models: list = device_deployer.get_device_models()
Azure_Function_Deployer = Azure_Function_Deployer(credentials, sitename= azfn_name, subscription_id=subscription_id, resource_group=resource_group)
Azure_Function_Deployer.create_azure_functions(device_models)

################################################################################################
# Remove Cached Credentials from Interactive Login
################################################################################################
#cached_credentials = os.path.join(os.path.expanduser('~'), '.azureml', 'auth')
#shutil.rmtree(cached_credentials)

print('Success! All resources required to have simulated csv data are up and running.')
print('For next steps to upgrade or scale out to more devices, please follow the Extended Guide README.')