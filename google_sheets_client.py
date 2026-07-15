import os
import pickle
import gspread
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Force change to script directory
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

load_dotenv()
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]
TOKEN_PATH = "token.pickle"
CREDS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "client_secret.json")

def get_client():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    # If credentials do not exist, or are invalid and cannot be refreshed, perform full authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Refresh failed, remove old credentials and force re-acquisition
                os.remove(TOKEN_PATH)
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            # When no token exists or refreshing is not needed/possible
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the updated credentials
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return gspread.authorize(creds)