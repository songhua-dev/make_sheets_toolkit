from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from shared.clean_data import process_batch

app = FastAPI()

FIELD_MAP = {"0": "Product Name", "1": "Price", "2": "Company", "3": "Tel", "4": "Location"}

@app.post("/process")
async def process_data(data_list: List[Dict[str, str]]):
    renamed = [{FIELD_MAP[k]: v for k, v in row.items()} for row in data_list]
    result = process_batch(renamed)
    return result