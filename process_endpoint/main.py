from fastapi import FastAPI
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.clean_data import process_batch

app = FastAPI()

# 接收一個列表，裡面包含多筆字典格式的數據
@app.post("/process")
async def process_data(data_list: List[Dict[str, Any]]):
    # 呼叫清洗邏輯
    result = process_batch(data_list)
    
    # 直接回傳結果給 Make.com
    return result