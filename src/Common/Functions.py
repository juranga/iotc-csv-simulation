from azure.storage.blob import BlockBlobService
from azureml.core.authentication import fetch_tenantid_from_aad_token
import json
import os
import uuid

# Generate UUID Password
def psw_generator():
    return str(uuid.uuid4())

# Return Json Dict from Json File
def load_json(file: str):
    with open(file, 'r') as json_file:
        return json.load(json_file)
