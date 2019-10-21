# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from azureml._base_sdk_common.common import fetch_tenantid_from_aad_token
import os
import sys
import json

from src.Common.Functions import load_json, psw_generator, write_to_config, get_object_id

# ARM Deployment class that uses Template/Parameter files to deploy to a resource group in a given subscription


class ARM_Deployer(object):

    def __init__(self, credentials, subscription_id: str,
                 template_dir: str, resource_group: str = None,
                 location: str = 'westus'):
        self.credentials = credentials
        self.subscription_id: str = subscription_id
        self.client = ResourceManagementClient(credentials, subscription_id)
        self.template_dir: str = template_dir
        self.resource_location: str = location
        self.parameters: dict = dict()
        self.resource_group = resource_group
        self.existing_resource_list: list = []
        self.create_resource_group()
        self.create_default_params()


    # Populates Parameters with default parameters found in Templates folder
    def create_default_params(self):
        param_file = os.path.join(self.template_dir, 'default.params.json')
        self.parameters = load_json(param_file)


    # Create resource group in specified subscription
    def create_resource_group(self):
        print('Creating or Updating Resource Group {}...'.format(self.resource_group))
        self.client.resource_groups.create_or_update(
            resource_group_name = self.resource_group,
            parameters = {
                'location': self.resource_location
            }
        )
        print('Finished... Moving on to deploying Resources.\n')


    # Loads Parameter File for Resource Deployment
    # This function loads any <template file>.params.json file first & compares its keys with the keys in
    # default.params.json. Any overlapping keys are then updated to the values in the default.params.json file.
    # 
    # The parameter Index must be provided based on the numeric id associated with param file.
    # This index is required because in order to update the parameter values of a Template File w/ the provided default values, 
    # We first need to load the default parameters for that param file found at that index.
    def load_parameters_from_file(self, param_file_path: str, param_idx: int):
        parameters: dict = load_json(param_file_path)
        default_params_at_idx: dict = self.parameters[str(param_idx)]

        # Location value must match the default parameters, and since it is universal across templates, can be outside the check.
        parameters['location'] = self.parameters['location']
        for key in parameters.keys():

            # If Template file has a param requirement satisfied from default params, update value
            if key in default_params_at_idx:
                parameters[key]['value'] = default_params_at_idx[key]['value']

            # Custom Configuration
            # Save storage account to config to be used in main deployment script.
            if key == 'storageAccountName':
                write_to_config({
                    'storageAccountName': parameters[key]['value']
                })

            # Programatically include tenant id & object id from user creating the resources.
            if key == 'tenantId':
                token = self.credentials._get_arm_token()
                parameters[key]['value'] = fetch_tenantid_from_aad_token(token)
            if key == 'objectId':
                client_id = 'https://vault.azure.net'
                token = self.credentials._get_arm_token_using_interactive_auth(resource=client_id)
                parameters[key]['value'] = get_object_id(token)

            # If Template param requires a password, make sure it adheres to Guid format
            key = key.lower()
            if 'password' in key:
                parameters['password']['value'] = psw_generator()

        return parameters


    # Deploys ARM Template
    # Loads JSON Template/Param Files in to dict object to feed to deployment client
    # If any error occurs, prints the error and ends the script.
    def deploy_template_from_file(self, template_file_path: str, param_file_path: str, template_idx: int):
        parameters: dict = self.load_parameters_from_file(param_file_path, template_idx)
        template: dict = load_json(template_file_path)
        deployment_properties = {
            'mode': DeploymentMode.incremental,
            'template': template,
            'parameters': parameters
        }
        try:
            deployment_async_operation = self.client.deployments.create_or_update(
                resource_group_name=self.resource_group,
                deployment_name=self.resource_group,
                properties=deployment_properties
            )
            deployment_async_operation.wait()
        except Exception as e:
            print("{}\n".format(e))
            print('It seems you have encountered an error in deployment of Azure Resources! \nPlease leave your error message as a github comment for the developers if you cannot solve the issue with personal debugging.')
            sys.exit()


    # Deploy all templates in the given Template Directory path
    # Each Template file MUST adhere to the following: `<numeric value>_<resource to deploy>.json`
    # Each Param file MUST adhere to the following: `<matching numeric value as template file>_<resource to deploy>.params.json`
    def deploy_all(self):

        # Get non-param template files and sort numerically
        # This is done so that dependency resources get deployed first
        template_files: list = []
        for file in sorted(os.listdir(self.template_dir)):
            if not 'params' in file:
                template_files.append(file)

        for idx, file in enumerate(template_files):
            template_file_name: str = file[:-5].split('_')[1]  # Remove .json and numeric id
            template_file_path: str = os.path.join(self.template_dir, file)
            param_file: str = '.'.join([file[:-5], 'params', 'json'])
            param_path: str = os.path.join(self.template_dir, param_file)
            
            if self.parameters[str(idx)]["exists"]:
                print("Skipping deployment of {} as this resource already exists...".format(template_file_name))
            else:
                print('Deploying {} to Resource Group {}. \nThis may take a few minutes...'.format(
                    template_file_name, self.resource_group))
                self.deploy_template_from_file(template_file_path=template_file_path,
                                    param_file_path=param_path, template_idx = idx)
