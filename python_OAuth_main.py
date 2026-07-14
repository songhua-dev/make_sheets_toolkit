import os
import gspread  # 必須加入此行以捕捉錯誤
from dotenv import load_dotenv
from google_sheets_client import get_client
from shared.clean_data import process_batch

load_dotenv()
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

def main():
    client = get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    
    # 讀取原始資料
    sheet = spreadsheet.worksheet("random_dirty_data2.csv")
    rows = sheet.get_all_records()

    # 執行清洗
    result = process_batch(rows)
    cleaned = result["cleaned_data"]

    if cleaned:
        # 確保工作表存在
        try:
            output_sheet = spreadsheet.worksheet("cleaned_data")
        except gspread.exceptions.WorksheetNotFound:
            output_sheet = spreadsheet.add_worksheet(title="cleaned_data", rows=300, cols=10)
        
        # 準備資料，確保每一行的順序與標題列一致
        headers = list(cleaned[0].keys())
        values = [headers] + [[row[h] for h in headers] for row in cleaned]
        
        # 清除舊資料並寫入新資料
        output_sheet.clear()
        output_sheet.update("A1", values)

    print(f"Total: {result['total_processed']}, Success: {result['success_count']}, Incomplete: {result['incomplete_count']}")

if __name__ == "__main__":
    main()