import os
import pickle
import gspread
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# 強制切換至腳本目錄
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

    # 如果憑證不存在，或者憑證無效且無法刷新，就進行完整授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # 刷新失敗，刪除舊憑證並強制重新取得
                os.remove(TOKEN_PATH)
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            # 沒有 token 或不需要/無法刷新時
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # 寫入更新後的憑證
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return gspread.authorize(creds)