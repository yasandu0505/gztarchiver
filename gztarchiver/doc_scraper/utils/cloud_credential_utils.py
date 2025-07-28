from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

# This permission scope lets your program access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# This function helps you log in and get credentials
def get_cloud_credentials(config):
    creds = None
    
    token_path = config["credentials"]["token_path"]
    client_secrets_path = config["credentials"]["client_secrets_path"]
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds