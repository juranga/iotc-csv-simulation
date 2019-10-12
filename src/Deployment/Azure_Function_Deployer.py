# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------


from azure.mgmt.web.web_site_management_client import WebSiteManagementClient


class Azure_Function_Deployer(object):

    def __init__(self, credentials, subscription_id: str, resource_group: str):
        self.resource_group = resource_group
        self.client = WebSiteManagementClient(credentials, subscription_id)

    # Create AzureFunctions Folder & Timer Trigger C# Azure Function 
    # for each Device Model in list of device models.
    def create_azure_functions(self, device_models: list):
        if not os.path.exists('AzureFunctions'):
            os.mkdir("AzureFunctions")
        functions_dir = os.path.join(os.getcwd(), "AzureFunctions")
        for model in device_models:
            csharp_class = {
                            '1': 'using Microsoft.Azure.IotCentral.Simulation;',
                            '2': '',
                            '3': '[FunctionName("{}Simulator")]'.format(model),
                            '4': 'public static void Run([TimerTrigger("0 */10 * * * * ")]TimerInfo myTimer, ILogger log)',
                            '5': '{',
                            '': {
                                '6': 'CsvDeviceSimulator simulator = new CsvDeviceSimulator();',
                                '7': 'simulator.SendTelemetryData("{}");'.format(model)
                            },
                            '8': '}'
                        }
            file = os.path.join(functions_dir, model)
            file = open('{}Simulator.cs'.format(file), 'w')
            self.write_json_to_csharp(file, csharp_class)
            file.close()

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
                    
    # TODO: Add Function to Zip Deploy the Azure Functions Folder
