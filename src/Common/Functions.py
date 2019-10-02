# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.storage.blob import BlockBlobService
from azureml.core.authentication import fetch_tenantid_from_aad_token
import json
import os
import uuid

from src.constants import CONFIG_PATH

# Generate UUID Password
def psw_generator():
    return str(uuid.uuid4())

# Return Json Dict from Json File
def load_json(file: str):
    with open(file, 'r') as json_file:
        return json.load(json_file)

def write_json(file: str, data: dict):
    with open(file, 'w+') as json_file:
        json.dump(data, json_file)

def write_to_config(options: dict):
    config = load_json(CONFIG_PATH)
    config.update(options)
    write_json(file=CONFIG_PATH, data=config)

    

