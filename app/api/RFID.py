from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
import asyncio

router = APIRouter(prefix="/RFID", tags=["RFID"])
templates = Jinja2Templates(directory="templates")

class WriteCardRequest(BaseModel):
    card_data: Dict
    save_to_db: bool = False

@router.get("/identify-rfid", response_class=HTMLResponse)
def identify_rfid(request: Request):
    return templates.TemplateResponse(request=request, name="RFID/identify-rfid.html", context={"message": "Identify RFID Card"})

@router.get("/write-uid", response_class=HTMLResponse)
def write_uid(request: Request):
    return templates.TemplateResponse(request=request, name="RFID/write-uid.html", context={"message": "Write UID to HF RFID CUID Card"})

@router.post("/setup-pn532")
async def setup_pn532(request: Request):
    return JSONResponse(content={"success": True, "message": "Demo mode: PN532 Simulated Setup OK"})

@router.post("/identify-rfid")
async def identify_rfid_post(request: Request):
    await asyncio.sleep(1.0)
    return JSONResponse(content={
        "success": True,
        "uid": "04A1B2C3",
        "type": "MIFARE Classic 1K",
        "sak": "08",
        "atqa": "04"
    })

@router.post("/write-uid")
async def write_uid_post(request: Request, write_request: WriteCardRequest):
    new_uid_hex = write_request.card_data.get("uid")
    if not new_uid_hex or len(new_uid_hex) != 8:
        return JSONResponse(content={"success": False, "error": "UID must be 8 hexadecimal characters"})
    await asyncio.sleep(1.0)
    return JSONResponse(content={"success": True, "message": f"Successfully wrote fake UID: {new_uid_hex}"})

@router.post("/analyze")
async def analyze_rfid(request: Request):
    return JSONResponse(content={
        "success": True,
        "module": "Demo Analyzer",
        "issues": ["Default Key Found (Demo)", "Weak Authentication"],
        "threat": {"score": 75, "status": "HIGH THREAT"}
    })
