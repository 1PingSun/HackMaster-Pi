from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from .mylib.WeakPasswordGenerater.main import PasswordGenerator
import os
import time
import json
import asyncio
from datetime import datetime
import random

router = APIRouter(
    prefix="/RFID",
    tags=["RFID"]
)

templates = Jinja2Templates(directory="templates")

RFID_DATA_DIR = "data/rfid"

# 定義寫入請求模型
class WriteCardRequest(BaseModel):
    card_data: Dict
    save_to_db: bool = False

# 定義請求模型
class SaveCardsRequest(BaseModel):
    cards: List[Dict]
    filename: str

# 模擬狀態變數，實際應用中可能需要更複雜的狀態管理
emulation_active = False
emulation_data = None
emulation_start_time = None
read_attempts = 0

# 定義模擬請求模型
class EmulationRequest(BaseModel):
    uid: str
    type: str
    data: str

@router.get("/rfid-learner", response_class=HTMLResponse)
def read_rfid_learner(request: Request):
    return templates.TemplateResponse(
        "RFID/rfid-learner.html",
        {"request": request, "message": "RFID Learner"}
    )

@router.get("/rfid-writer", response_class=HTMLResponse)
def read_rfid_writer(request: Request):
    return templates.TemplateResponse(
        "RFID/rfid-writer.html",
        {"request": request, "message": "RFID Writer"}
    )

@router.post("/read")
async def read_rfid_card():
    """
    讀取RFID卡片資料
    """
    try:
        # 這裡模擬讀取RFID卡片的操作
        # 實際使用時應該連接RFID讀卡器
        
        # 模擬延遲
        await asyncio.sleep(2)
        
        # 模擬讀取數據（這部分需要替換為實際讀卡邏輯）
        uid = ''.join([random.choice('0123456789ABCDEF') for _ in range(8)])
        
        return {
            "success": True,
            "uid": uid,
            "type": "Mifare Classic 1K",
            "data": f"Sample data block for card {uid[:4]}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/save")
async def save_rfid_cards(request: SaveCardsRequest):
    """
    儲存RFID卡片集合為JSON檔案
    """
    try:
        # 確保目錄存在
        os.makedirs(RFID_DATA_DIR, exist_ok=True)
        
        # 建立檔案名稱
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.filename}_{timestamp}.json"
        filepath = os.path.join(RFID_DATA_DIR, filename)
        
        # 寫入JSON檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(request.cards, f, ensure_ascii=False, indent=2)
        
        # 返回成功訊息和下載URL
        return {
            "success": True,
            "message": f"Cards saved to {filename}",
            "filename": filename,
            "download_url": f"/RFID/download/{filename}"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/download/{filename}")
async def download_rfid_file(filename: str):
    """
    下載儲存的RFID卡片JSON檔案
    """
    filepath = os.path.join(RFID_DATA_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/json'
        )
    return JSONResponse(
        status_code=404,
        content={"message": "File not found"}
    )

@router.post("/write")
async def write_rfid_card(request: WriteCardRequest):
    """
    將數據寫入RFID卡片
    """
    try:
        # 這裡應該實現實際的RFID卡片寫入邏輯
        # 以下僅為模擬寫入操作
        
        # 模擬延遲
        await asyncio.sleep(3)
        
        # 取得要寫入的卡片數據
        card_data = request.card_data
        uid = card_data.get('uid', '')
        data = card_data.get('data', '')
        card_type = card_data.get('type', 'Unknown')
        
        # 這裡是實際寫入邏輯的地方（需要根據硬體實現）
        # ...
        
        # 模擬寫入結果
        written_uid = uid if uid else '1A2B3C4D5E6F'
        
        return {
            "success": True,
            "message": "Card write operation completed successfully",
            "written_uid": written_uid,
            "sectors_written": "0-15",
            "type": card_type
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
    
@router.get("/rfid-emulator", response_class=HTMLResponse)
def read_rfid_emulator(request: Request):
    return templates.TemplateResponse(
        "RFID/rfid-emulator.html",
        {"request": request, "message": "RFID Emulator"}
    )

@router.post("/emulate/start")
async def start_rfid_emulation(data: EmulationRequest):
    """
    開始 RFID 卡片模擬
    """
    global emulation_active, emulation_data, emulation_start_time, read_attempts
    
    try:
        # 檢查是否已在模擬中
        if emulation_active:
            return {"success": False, "message": "Emulation already active. Stop current emulation first."}
        
        # 這裡實現啟動 RFID 模擬的邏輯
        # 實際上，需要根據硬體功能啟動 NFC 卡片模擬
        
        # 模擬延遲啟動
        await asyncio.sleep(2)
        
        # 儲存模擬資料
        emulation_data = {
            "uid": data.uid,
            "type": data.type,
            "data": data.data
        }
        
        # 更新狀態
        emulation_active = True
        emulation_start_time = time.time()
        read_attempts = 0
        
        return {
            "success": True,
            "message": "RFID emulation started successfully",
            "uid": data.uid,
            "type": data.type
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/emulate/stop")
async def stop_rfid_emulation():
    """
    停止 RFID 卡片模擬
    """
    global emulation_active, emulation_data, emulation_start_time
    
    try:
        # 檢查是否有模擬在運行
        if not emulation_active:
            return {"success": False, "message": "No active emulation to stop"}
        
        # 這裡實現停止 RFID 模擬的邏輯
        # 實際上，需要根據硬體功能停止 NFC 卡片模擬
        
        # 模擬延遲
        await asyncio.sleep(1)
        
        # 更新狀態
        emulation_active = False
        emulation_data = None
        
        # 計算運行時間
        runtime = 0
        if emulation_start_time:
            runtime = int(time.time() - emulation_start_time)
            emulation_start_time = None
        
        return {
            "success": True,
            "message": "RFID emulation stopped successfully",
            "runtime": runtime,
            "read_attempts": read_attempts
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/emulate/stats")
async def get_emulation_stats():
    """
    獲取 RFID 模擬的統計資訊
    """
    global emulation_active, emulation_start_time, read_attempts
    
    try:
        # 檢查是否有模擬在運行
        if not emulation_active:
            return {"success": False, "message": "No active emulation"}
        
        # 在實際應用中，這裡應該從硬體或服務中獲取真實統計資料
        # 這裡我們模擬偶爾增加讀取嘗試次數
        if random.random() < 0.3:  # 30% 的機率增加讀取嘗試
            read_attempts += 1
        
        # 計算運行時間
        runtime = 0
        if emulation_start_time:
            runtime = int(time.time() - emulation_start_time)
        
        return {
            "success": True,
            "active": emulation_active,
            "runtime": runtime,
            "read_attempts": read_attempts,
            "last_activity": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "message": str(e)}