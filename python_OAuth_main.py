import os
import gspread  # Must include this line to catch errors
from dotenv import load_dotenv
from google_sheets_client import get_client
from shared.clean_data import process_batch

load_dotenv()
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

def main():
    client = get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    
    # Read raw data
    sheet = spreadsheet.worksheet("random_dirty_data2.csv")
    rows = sheet.get_all_records()

    # Execute cleaning
    result = process_batch(rows)
    cleaned = result["cleaned_data"]

    if cleaned:
        # Ensure the worksheet exists
        try:
            output_sheet = spreadsheet.worksheet("cleaned_data")
        except gspread.exceptions.WorksheetNotFound:
            output_sheet = spreadsheet.add_worksheet(title="cleaned_data", rows=300, cols=10)
        
        # Prepare data, ensuring the order of each row matches the header row
        headers = list(cleaned[0].keys())
        values = [headers] + [[row[h] for h in headers] for row in cleaned]
        
        # Clear old data and write new data
        output_sheet.clear()
        output_sheet.update("A1", values)

    print(f"Total: {result['total_processed']}, Success: {result['success_count']}, Incomplete: {result['incomplete_count']}")

if __name__ == "__main__":
    main()