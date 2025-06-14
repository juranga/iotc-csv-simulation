# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------


import hmac, base64, hashlib
import time, datetime
import requests, json, urllib

from src.Common.Functions import unix_time_millis

class Dps_Keygen(object):

    def __init__(self):
        self.iot_hub = None

    # python version of: https://github.com/Azure/dps-keygen/blob/master/dps.js
    def register_device_on_hub(self, device_id, scope_id, sas_key, api_version):
        expires = int( ( unix_time_millis(datetime.datetime.utcnow()) + (50 * 1000) )  / 1000 ) # 50 secs

        sr = '{}%2fregistrations%2f{}'.format(scope_id, device_id)
        regId = '{}\n{}'.format(sr, expires)
        key = base64.b64decode(sas_key.encode('utf-8'))
        sigEncoded = urllib.parse.quote(
                base64.b64encode(
                hmac.HMAC(key, regId.encode('utf-8'), hashlib.sha256).digest()
            )
        ).replace('/', '%2F')

        data = {
            'registrationId': device_id
        }

        headers = {
            'Authorization': 'SharedAccessSignature sig={}&se={}&skn={}&sr={}'.format(sigEncoded,expires,'registration',sr),
            'Accept':'application/json',
            'Content-Type':'application/json',
            'UserAgent':'prov_device_client/1.0',
            'Connection':'keep-alive'
        }

        resp = requests.put('https://global.azure-devices-provisioning.net/{}/registrations/{}/register?api-version={}'.format(scope_id, device_id, api_version),  headers=headers, json=data)

        if resp.status_code == 200 or resp.status_code == 202:
            return [headers, json.loads(resp.content)['operationId']]
        return None

    # python version of: https://github.com/Azure/dps-keygen/blob/master/dps.js
    def generate_connection_string(self, device_id, scope_id, sas_key):

        # If iot hub identity has yet to be obtained, api calls to register & obtain the iot hub name are required
        # The logic code below is the dps-keygen logic
        api_version = '2018-11-01'
        resp = self.register_device_on_hub(device_id, scope_id, sas_key, api_version)
        if not resp == None :
            headers = resp[0]
            operation_id = resp[1] 
            # Loop waiting on Status of Device Provisioning
            while True:
                uri = 'https://global.azure-devices-provisioning.net/{}/registrations/{}/operations/{}?api-version={}'.format(scope_id, device_id, operation_id, api_version)
                resp = requests.get(uri, headers=headers)
                if resp.status_code == 200 or resp.status_code == 202:
                    data = json.loads(resp.content)
                    if data['status'] == 'assigned':
                        data = data['registrationState']
                        self.iot_hub = data['assignedHub']
                        return 'HostName={};DeviceId={};SharedAccessKey={}'.format(self.iot_hub, device_id, sas_key)
                    elif data['status'] == 'assigning':
                        # Assume Device will be assigned, therefore do not sleep for 1.2 seconds until next call.
                        # This is done to scale the # of devices as desired, and not wait until each device is confirmed registered.
                        # Otherwise, each device created will take 1 second.. therefore 60 devices = 1 minutes. 120 devices = 2 mins.. etc
                        # Scale testing could suffer? TODO: Figure out what is preferred for this
                        if not self.iot_hub == None:
                            return 'HostName={};DeviceId={};SharedAccessKey={}'.format(self.iot_hub, device_id, sas_key)
                        time.sleep(1.3)
                    elif data['status'] == 'failed':
                        print('Authenticating device {} has failed. Skipping its deployment.'.format(device_id))
                        return 
                # Failed Get Request
                else:
                    print("Generating Connection String failed.")
                    print(resp.content)
                    return None
        return None
