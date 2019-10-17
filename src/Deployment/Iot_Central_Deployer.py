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
from collections import defaultdict

class Iot_Central_Deployer(object): 

    def __init__(self, credentials, app_domain_name: str):

        self.app_domain_name = app_domain_name
        self.credentials = credentials
        self.api_version = 'preview'
        self.url = 'https://{}.azureiotcentral-dev.com/api/{}'.format(self.app_domain_name, self.api_version)
        self.auth_token = 'SharedAccessSignature sr=bd5de8a9-3bcb-4415-a75d-ebb5231d301a&sig=K43pzKcrAgafjXcZ%2BWU1mLGBx4jgN4g13sh8UeSpiqI%3D&skn=testingPrivateJerry&se=1602952228452'
        self.header = {
            'Authorization': self.auth_token,
            'Content-Type': 'application/json'
        }
        self.existing_models = self.get_existing_models()
        self.dps_keygen = Dps_Keygen()

    def get_auth_token(self):
        central_url = 'https://apps.azureiotcentral.com'
        token = self.credentials._get_arm_token_using_interactive_auth(resource=central_url)
        return 'Bearer ' + token

    # Existing Models are stored as dictionary objects 
    # to easily check if a model already exists when deploying, and for ease of access to
    # the interface id which is used to create new simulated devices.
    def get_existing_models(self):
        print('Getting Existing models...')
        existing_models = defaultdict(dict)
        models_url = '{}/models/'.format(self.url)
        resp = requests.get(models_url, headers=self.header)
        if resp.status_code == 200 or resp.status_code == 202:
            model_list = json.loads(resp.content)['value']
            for model in model_list:
                # Saves the model name & the interface instance id.
                # This is required for when creating new devices of this model
                existing_models[model['displayName']]['id'] = model['@id']
        return existing_models

    # Deploys the models in the DeviceModels folder
    def deploy_models(self, models_dir: str):
        print('Deploying Models to IoT Central...')
        models_url = '{}/models/'.format(self.url)
        for model_file_name in os.listdir(models_dir):
            model_file_path = os.path.join(models_dir, model_file_name)
            model = load_json(model_file_path)

            # Check if model already exists in existing models
            # If it does, skip deploying that model 
            if model['displayName'] in self.existing_models.keys():
                continue
            resp = requests.post(models_url, headers=self.header, json=model)
        # Reset the existing models to store modelDefinitions set by Iot Central
        self.existing_models = self.get_existing_models()

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

    # Returns True if Device Creation was Successful or Device already exists
    def create_device(self, device_id: str, device_model: str):
        print('Creating Device {}'.format(device_id))
        devices_url = '{}/devices/'.format(self.url)
        if self.is_existing_device(device_id):
            print("Skipping deployment of device {}, as it already exists.\n".format(device_id))
            return False
        # Instance of is obtained by parsing the Model's interface id
        # Example: "urn:iotcentral:model" is expected
        instance_of = self.existing_models[device_model]['id']
        device = {
                '@type': 'Device',
                'id': device_id,
                'displayName': device_id,
                'instanceOf': instance_of,
                'simulated': False,
                'approved': True,
                'deviceId': device_id
            }
        resp = requests.post(devices_url, headers=self.header, json=device)
        return resp.status_code == 200 or resp.status_code == 201

