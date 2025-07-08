from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from .mylib.WeakPasswordGenerater.main import PasswordGenerator
from .mylib.RFIDlib import main as RFIDlib
import os
import time
import json
import asyncio
from datetime import datetime
import random
import binascii

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

@router.get("/identify-rfid", response_class=HTMLResponse)
def identify_rfid(request: Request):
    return templates.TemplateResponse(
        "RFID/identify-rfid.html",
        {"request": request, "message": "Identify RFID Card"}
    )

@router.get("/write-uid", response_class=HTMLResponse)
def write_uid(request: Request):
    return templates.TemplateResponse(
        "RFID/write_uid.html",
        {"request": request, "message": "Write UID to HF RFID CUID Card"}
    )

@router.post("/setup-pn532")
async def setup_pn532(request: Request):
    try:
        result = RFIDlib.setup()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})

@router.post("/identify-rfid")
async def identify_rfid_post(request: Request):
    try:
        found = RFIDlib.iso14443a_identify()
        while not found["success"]:
            await asyncio.sleep(0.1)
            found = RFIDlib.iso14443a_identify()
        return JSONResponse(content=found)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})
    
@router.post("/write-uid")
async def write_uid_post(request: Request, write_request: WriteCardRequest):
    try:
        new_uid_hex = write_request.card_data.get("uid")
        if not new_uid_hex:
            return JSONResponse(content={"success": False, "error": "UID is required"})
        
        if len(new_uid_hex) != 8:
            print("❌ UID UID must be 8 hexadecimal characters")
            return JSONResponse(content={"success": False, "error": "UID must be 8 hexadecimal characters"})
        
        try:
            binascii.unhexlify(new_uid_hex)
        except:
            print("❌ UID contains invalid characters")
            return JSONResponse(content={"success": False, "error": "UID contains invalid characters"})
        
        result = RFIDlib.write_uid(new_uid_hex)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})