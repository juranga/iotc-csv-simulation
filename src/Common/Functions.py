# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from azure.storage.blob import BlockBlobService
from azureml.core.authentication import fetch_tenantid_from_aad_token
import datetime
import json
import os
import uuid
import jwt

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

    
def unix_time_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000.0

def get_object_id(token):
    decode_json = jwt.decode(token, verify=False)
    return decode_json['oid']

def get_unique_resource_id(resource):
    first_half = str(uuid.uuid4().fields[-1])[:5]
    second_half = str(uuid.uuid4().fields[-1])[:5]
    return resource + first_half + second_half
