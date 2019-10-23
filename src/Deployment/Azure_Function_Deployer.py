# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.mgmt.web.web_site_management_client import WebSiteManagementClient
import os
import shutil, requests, zipfile
import json

from src.Common.Functions import write_json
from src.constants import AZURE_FUNCTIONS_PATH


class Azure_Function_Deployer(object):

    def __init__(self, credentials, sitename: str, subscription_id: str, resource_group: str):
        self.credentials = credentials
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self.sitename = sitename

    # Insert App Settings
    # This exists in the scenario where secrets are not desired to be kept in KeyVault
    def insert_app_setting(self, settings):
        client = WebSiteManagementClient(self.credentials, self.subscription_id)
        header = {'Authentication': 'Bearer ' + self.credentials._get_arm_token_using_interactive_auth("https://login.windows.net")}
        azure_func_settings = client.web_apps.list_application_settings(self.resource_group, self.sitename)
        for key in settings:
            azure_func_settings[key] = settings[key]
        client.web_apps.update_application_settings(self.resource_group, self.sitename, properties=azure_func_settings)
               
    # Authentication required for Zip Deploying to Azure Functions
    # Zip Deploy does not authenticate with bearer tokens. It requires
    # getting the Publishing Profile username and password, which is difficult to obtain unless
    # you do an xml hack. The following code parses the xml publishing profile & creates the authentication
    def authenticate_to_zipdeploy(self):
        import xmltodict
        client = WebSiteManagementClient(self.credentials, self.subscription_id)
        xml_publish_profile = client.web_apps.list_publishing_profile_xml_with_secrets(self.resource_group, self.sitename)
        for data in xml_publish_profile:
            json_publish_profile = xmltodict.parse(data)

        publish_name = json_publish_profile['publishData']['publishProfile'][0]['@userName']
        publish_psw = json_publish_profile['publishData']['publishProfile'][0]['@userPWD']

        return (publish_name, publish_psw)

    def deploy_azure_functions(self):
        shutil.make_archive('functions', 'zip', AZURE_FUNCTIONS_PATH)
        print('Deploying Azure Function through Zip Deploy... This may take a couple of minutes.')
  
        # Creates the Headers for Authorization
        headers = {
            'Content-Type': 'application/octet-stream'
        }

        # Opens Zip File & sends the binary data via REST call to Azure Functions
        zip_api_url = 'https://{}.scm.azurewebsites.net/api/zipdeploy'.format(self.sitename)
        zipfile = open('./functions.zip', 'rb').read()
        resp = requests.post(zip_api_url, headers=headers, data=zipfile, auth=self.authenticate_to_zipdeploy())

        # Removes Zip File after deployment done
        os.remove('./functions.zip')

    # Create Timer Trigger C# Azure Functions 
    # for each Device Model in list of device models.
    def create_azure_functions(self, device_models: list):
        directories_to_remove = []
        for model in device_models:
            function_name = '{}Simulator'.format(model)
            csharp_class = {
                            '1': '',
                            '2': '',
                            '4': 'public static void Run([TimerTrigger("0 */5 * * * * ")]TimerInfo myTimer)',
                            '5': '{',
                            '': {
                                '6': 'CsvDeviceSimulator simulator = new CsvDeviceSimulator();',
                                '7': 'simulator.SendTelemetryDataOfType("{}");'.format(model)
                            },
                            '8': '}'
                        }

            # Create a temporary Azure Function folder to populate with dependencies required
            function_folder = os.path.join(AZURE_FUNCTIONS_PATH, function_name)
            if not os.path.exists(function_folder):
                os.mkdir(function_folder)
            shutil.copy(os.path.join(AZURE_FUNCTIONS_PATH,'function.proj'), function_folder)
            self.create_function_dependencies(function_name, function_folder)

            # Copy the CsvDeviceSimulator class & place it in to newly created Azure Function folder
            template_simulator_path = os.path.join(AZURE_FUNCTIONS_PATH, 'CsvDeviceSimulator.cs')
            shutil.copy(template_simulator_path, function_folder)

            # Append the Azure Function Timer Trigger to the Simulator template class
            # and rename the copied function class to 'run.csx' to work in Azure Functions
            function_file = os.path.join(function_folder, 'CsvDeviceSimulator.cs')
            renamed_file = os.path.join(function_folder, 'run.csx')
            file = open(function_file, 'a')
            self.write_json_to_csharp(file, csharp_class)
            file.close()
            
            os.rename(function_file, renamed_file)
            directories_to_remove.append(function_folder)

        # Zip Deploy Azure Functions that were just created
        self.deploy_azure_functions()
        # Remove the Functions after deployment
        for folder in directories_to_remove:
            shutil.rmtree(folder)
        
    # Create the bindings required by every Azure Function 
    def create_function_dependencies(self, function_name: str, file_path: str):
        function_json_file = {
            "bindings": [
                {
                    "authLevel": "function",
                    "name": "myTimer",
                    "type": "timerTrigger",
                    "direction": "in",
                    "schedule": "0 */15 * * * *"
                }
            ]
        }
        file_name = os.path.join(file_path, 'function.json')
        write_json(file_name, function_json_file)


    # Naive way to create a Csharp Class from a json dictionary.
    # Recursively iterates through nested inner objects and
    # each nested object indicates a tab spacing in the c# class.
    # File must be an opened IO file.
    def write_json_to_csharp(self, file, json_obj: dict, inner_dict_key: str= None, n_tabs: int= 0):
        if inner_dict_key == None:
            for key in json_obj.keys():
                if type(json_obj[key]) == dict:
                    self.write_json_to_csharp(file, json_obj, inner_dict_key= key, n_tabs=1)
                else:
                    file.write(json_obj[key] + '\n')
        else:
            for key in json_obj[inner_dict_key].keys():
                inner_dict = json_obj[inner_dict_key]
                if type(inner_dict[key]) == dict:
                    self.write_json_to_csharp(file, inner_dict, inner_dict_key= key, n_tabs= n_tabs+1)
                else:
                    tabs = ['\t' for x in range(0, n_tabs)]
                    line_to_write = ''.join(tabs[0:n_tabs]) + inner_dict[key] + '\n'
                    file.write(line_to_write)
