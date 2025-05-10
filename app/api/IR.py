# 建議的後端 API 實現 (IR.py)

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Optional, List
import asyncio
import json
import time
from datetime import datetime
import os

router = APIRouter(
    prefix="/IR",
    tags=["IR"]
)

templates = Jinja2Templates(directory="templates")

# 紅外線錄製狀態變數
ir_recording = False
ir_signal = None
ir_record_start_time = None

class TransmitRequest(BaseModel):
    signalData: str
    format: Optional[str] = "RAW"

@router.get("/signal-learner", response_class=HTMLResponse)
def read_signal_learner(request: Request):
    return templates.TemplateResponse(
        "IR/signal-learner.html",
        {"request": request, "message": "IR Signal Learner"}
    )

@router.get("/signal-enumerator", response_class=HTMLResponse)
def read_signal_enumerator(request: Request):
    return templates.TemplateResponse(
        "IR/signal-enumerator.html",
        {"request": request, "message": "IR Signal Enumerator"}
    )

@router.post("/record")
async def record_ir_signal():
    """
    開始錄製紅外線訊號
    """
    global ir_recording, ir_signal, ir_record_start_time
    
    try:
        # 檢查是否已在錄製
        if ir_recording:
            return {"success": False, "message": "Already recording"}
        
        # 這裡實現啟動 IR 接收器的代碼
        # 以下僅為模擬，實際使用需要連接硬體
        
        # 更新狀態
        ir_recording = True
        ir_signal = None
        ir_record_start_time = time.time()
        
        # 啟動背景任務等待訊號
        # 在實際應用中，這應該與硬體互動
        asyncio.create_task(simulate_ir_reception())
        
        return {"success": True, "message": "IR recording started"}
    except Exception as e:
        ir_recording = False
        return {"success": False, "message": str(e)}

@router.post("/record/cancel")
async def cancel_ir_recording():
    """
    取消錄製紅外線訊號
    """
    global ir_recording, ir_signal
    
    try:
        # 更新狀態
        ir_recording = False
        ir_signal = None
        
        return {"success": True, "message": "Recording cancelled"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/status")
async def get_ir_status():
    """
    獲取紅外線錄製狀態
    """
    global ir_recording, ir_signal, ir_record_start_time
    
    # 檢查是否超時
    if ir_recording and ir_record_start_time:
        if time.time() - ir_record_start_time > 15:  # 15秒超時
            ir_recording = False
            return {"status": "timeout", "message": "Recording timed out"}
    
    if ir_recording:
        return {"status": "recording"}
    elif ir_signal:
        return {
            "status": "completed",
            "signal": ir_signal
        }
    else:
        return {"status": "idle"}

@router.post("/transmit")
async def transmit_ir_signal(request: TransmitRequest):
    """
    發送紅外線訊號
    """
    try:
        # 這裡實現發送 IR 訊號的代碼
        # 以下僅為模擬，實際使用需要連接硬體
        
        # 模擬發送延遲
        await asyncio.sleep(1)
        
        return {"success": True, "message": "Signal transmitted successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 模擬紅外線接收
async def simulate_ir_reception():
    global ir_recording, ir_signal
    
    # 模擬 3 秒後接收到訊號
    await asyncio.sleep(3)
    
    # 如果仍在錄製狀態，則模擬接收到訊號
    if ir_recording:
        ir_signal = {
            "data": "010101010110101010100101010101011010101010010101010101101010",
            "format": "NEC",
            "length": 32
        }
        ir_recording = False

@router.post("/enumerate")
async def enumerate_ir_code(data: dict):
    """
    枚舉並發送紅外線代碼，嘗試控制設備
    """
    try:
        device_type = data.get("device_type")
        brand = data.get("brand", "")
        protocol = data.get("protocol", "all")
        function = data.get("function")
        code_index = data.get("code_index", 0)
        
        # 在實際應用中，這裡應該根據設備類型、品牌和功能生成特定的IR代碼
        # 然後通過紅外線發射器發送
        
        # 模擬發送代碼
        await asyncio.sleep(0.1)
        
        # 模擬代碼，實際應用需改為真實生成
        code_hex = generate_ir_code(device_type, brand, protocol, function, code_index)
        
        # 在實際應用中，這裡應該檢測設備是否響應了信號
        # 可通過額外的傳感器或用戶確認
        
        # 模擬隨機響應（實際應用中需要真實響應檢測）
        response_detected = random.random() < 0.05  # 5% 的概率模擬成功
        
        return {
            "success": True,
            "code_index": code_index,
            "code_hex": code_hex,
            "protocol": protocol if protocol != "all" else random.choice(["NEC", "SONY", "RC5", "RC6", "SAMSUNG"]),
            "response": response_detected,
            "bits": 32  # 大多數紅外線代碼的長度
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# 輔助函數：生成紅外線代碼（示例）
def generate_ir_code(device_type, brand, protocol, function, index):
    # 實際應用需要使用真實代碼數據庫或算法生成有效代碼
    # 這只是一個簡單的示例實現
    base_value = index * 37 + ord(function[0])  # 簡單算法生成不同代碼
    return format(base_value % 65536, '04X') + format((base_value * 17) % 65536, '04X')