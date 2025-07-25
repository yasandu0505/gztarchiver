from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

# This permission scope lets your program access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# This function helps you log in and get credentials
def get_cloud_credentials():
    creds = None
    if os.path.exists('credentials/token.json'):
        creds = Credentials.from_authorized_user_file('credentials/token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials/credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('credentials/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds