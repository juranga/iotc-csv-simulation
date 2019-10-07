# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import requests
import os, json

from src.Common.Functions import load_json

class Iot_Central_Deployer(object): 

    def __init__(self, app_domain_name, auth_token):

        self.app_domain_name = app_domain_name
        self.auth_token = auth_token
        self.api_version = 'preview'
        self.header = {
            "Authorization": "Bearer " + self.auth_token,
            "Content-Type": "application/json"
        }
        self.existing_models = []
        self.models_url = 'https://{}.azureiotcentral.com/api/{}/models/'.format(self.app_domain_name, self.api_version)
        self.get_existing_models()

    # Existing Models need to be cached to easily check if a model already exists when deploying.
    def get_existing_models(self):
        resp = requests.get(self.models_url, headers=self.header)
        if resp.status_code < 300 or resp.status_code >= 200:
            model_list = json.loads(resp.content)['value']
            for model in model_list:
                self.existing_models.append(model['displayName'])


    def deploy_models(self, models_dir: str):
        for model_file_name in os.listdir(models_dir):
            model_file_path = os.path.join(os.getcwd(), 'deviceModels', model_file_name)
            model = load_json(model_file_path)

            # Check if model already exists in existing models
            # If it does, skip deploying that model 
            if model['displayName'] in self.existing_models:
                continue

            resp = requests.post(self.models_url, headers=self.header, json=model)
            # Basic Error Check TODO: potentially update this.
            if resp.status_code >= 300 or resp.status_code < 200:
                print(resp.content)

    def deploy_device(self, device_id, device_model):
        device = {
                    "@type": "string",
                    "displayName": "",
                    "description": "",
                    "comment": "",
                    "instanceOf": device_model,
                    "simulated": False,
                    "deviceId": device_id,
                    "approved": True
                }
        resp = requests.post(self.models_url, headers=self.header, json=device)
        if not resp.status_code == 201:
            print('Device {} Malformed.'.format(device_id))
        return

