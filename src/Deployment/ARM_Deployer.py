# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
import os, sys, json

from src.Common.Functions import load_json, psw_generator

# ARM Deployment class that uses Template/Param files to deploy to a resource group in a given subscription
class ARM_Deployer(object):

    def __init__(self, credentials, subscription_id: str,
                 resource_group: str, template_dir: str,
                 location: str = 'westus'):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.client = ResourceManagementClient(credentials, subscription_id)
        self.template_dir = template_dir
        self.location = location
        self.parameters = dict()

        self.create_default_params()
        self.create_resource_group()

    # Populates Parameters  with default params in Templates folder
    def create_default_params(self):
        param_file = os.path.join(self.template_dir, 'default.params.json')
        self.parameters = load_json(param_file)

    # Create resource group in subscription
    def create_resource_group(self):
        print('Creating Resource Group {}...'.format(self.resource_group))
        self.client.resource_groups.create_or_update(
            self.resource_group,
            {
                'location': self.location
            }
        )
        print('Finished creating Resource Group.\n')

    # Load Parameter Files
    # Updates Password parameters to adhere to Guid format & increase security.
    def load_parameters(self, param_file: str):
        parameters: dict = load_json(param_file)
        for key in parameters.keys():
            if key in self.parameters:
                parameters[key]['value'] = self.parameters[key]['value']
            key = key.lower()
            if 'password' in key:
                parameters['password']['value'] = psw_generator()

        return parameters

    # Deploy ARM Template
    # Loads JSON Template/Param Files in to dict and feed to deployment client
    def deploy_template(self, template_file: str, param_file: str, resource_name: str):
        parameters: dict = self.load_parameters(param_file)
        template: dict = load_json(template_file)
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
            print(e)
            print("An error occurred during deployment... Deleting Resource Group")
            delete_async_operation = self.client.resource_groups.delete(self.resource_group)
            delete_async_operation.wait()
            print('Completed deleting Resource Group.\nPlease leave a message as a github comment for the developers if you cannot solve the issue with personal debugging.')
            sys.exit()

    # Deploy all templates in specified path.
    # Each Template file MUST adhere to the following: `<numeric value>_<resource to deploy>.json`
    # Each Param file MUST adhere to the following: `<matching numeric value as template file>_<resource to deploy>.params.json`
    def deploy_all(self):

        # Get non-param template files and sort numerically
        template_files: list = sorted([file for file in os.listdir(
            self.template_dir) if not ('params' in file)])

        for file in template_files:
            file_name = file[:-5].split('_')[1]  # Remove .json and numeric id
            file_path = os.path.join(self.template_dir, file)
            param_file: str = '.'.join([file[:-5], 'params', 'json'])
            param_path = os.path.join(self.template_dir, param_file)
            print('Deploying {} to Resource Group {}. \nThis may take a few minutes...'.format(
                file_name, self.resource_group))
            self.deploy_template(template_file=file_path, param_file=param_path, resource_name=file_name)
