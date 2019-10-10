# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------


from azure.mgmt.web.web_site_management_client import WebSiteManagementClient


class Azure_Function_Deployer(object):

    def __init__(self, credentials, subscription_id: str, resource_group: str):
        self.resource_group = resource_group
        self.client = WebSiteManagementClient(credentials, subscription_id)

    # Insert App Settings
    def insert_app_setting(self, settings):
        azure_func_settings = self.client.web_apps.list_application_settings(self.resource_group, 'customsimazfn')
        for key in settings:
            azure_func_settings[key] = settings[key]
        self.client.web_apps.update_application_settings(self.resource_group, 'iotcustomsimulationazfn', properties=azure_func_settings)

    # TODO: Add Function to Zip Deploy the Azure Functions Folder
