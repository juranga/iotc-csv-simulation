
import json
from azureml.core.authentication import InteractiveLoginAuthentication

creds = InteractiveLoginAuthentication(force=False, tenant_id=None)
print(creds)


