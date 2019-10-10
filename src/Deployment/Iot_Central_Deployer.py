# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

import base64
import requests
import os, json, datetime
import time
import urllib.parse
import hmac
import hashlib

from src.Common.Functions import load_json, unix_time_millis
from src.Common.Dps_Keygen import Dps_Keygen

class Iot_Central_Deployer(object): 

    def __init__(self, credentials, app_domain_name: str):

        self.app_domain_name = app_domain_name
        self.credentials = credentials
        self.api_version = 'preview'
        self.url = 'https://{}.azureiotcentral.com/api/{}/'.format(self.app_domain_name, self.api_version)
        self.existing_models = self.get_existing_models()
        self.auth_token = self.get_auth_token()
        self.header = {
            'Authorization': 'Bearer ' + self.auth_token,
            'Content-Type': 'application/json'
        }
        self.dps_keygen = Dps_Keygen()

    def get_auth_token(self):
        central_url = 'https://apps.azureiotcentral.com'
        token = self.credentials._get_arm_token_using_interactive_auth(resource=central_url)
        return token

    # Existing Models need to be stored to easily check if a model already exists when deploying.
    def get_existing_models(self):
        models = []
        models_url = '{}/models'.format(self.url)
        resp = requests.get(models_url, headers=self.header)
        if resp.status_code == 200 or resp.status_code == 202:
            model_list = json.loads(resp.content)['value']
            for model in model_list:
                models.append(model['displayName'])
        return models

    # Get Device Scope Id and Primary Key from IoT Central
    def get_device_connection_string(self, device_id: str):
        device_key_url = '{}/devices/{}/credentials'.format(self.url, device_id)
        resp = requests.get(device_key_url, headers=self.header)
        if resp.status_code == 200 or resp.status_code == 202:
            device_credentials = json.loads(resp.content)
            scope_id = device_credentials['scopeId']
            sas_key = device_credentials['symmetricKey']['primaryKey']
            return self.dps_keygen.generate_connection_string(device_id=device_id, scope_id=scope_id, sas_key=sas_key)

        return None

    # Returns if Device already exists in Central Application
    def is_existing_device(self, device_id: str):
        devices_url = '{}/devices/{}'.format(self.url, device_id)
        resp = requests.get(devices_url, headers=self.header)
        return resp.status_code == 200 or resp.status_code == 202
        
    # Deploys the models in the DeviceModels folder
    def deploy_models(self, models_dir: str):
        models_url = self.url + 'models/' 
        for model_file_name in os.listdir(models_dir):
            model_file_path = os.path.join(os.getcwd(), 'deviceModels', model_file_name)
            model = load_json(model_file_path)

            # Check if model already exists in existing models
            # If it does, skip deploying that model 
            if model['displayName'] in self.existing_models:
                continue
            resp = requests.post(models_url, headers=self.header, json=model)

    # Returns True if Device Creation was Successful or Device already exists
    def deploy_device(self, device_id: str, device_model: str):
        devices_url = '{}/devices/'.format(self.url)
        if self.is_existing_device(device_id):
            return True
        device = {
                    '@type': 'string',
                    'displayName': '',
                    'description': '',
                    'comment': '',
                    'instanceOf': device_model,
                    'simulated': False,
                    'deviceId': device_id,
                    'approved': True
                }
        resp = requests.post(devices_url, headers=self.header, json=device)
        return resp.status_code == 200 or resp.status_code == 202

