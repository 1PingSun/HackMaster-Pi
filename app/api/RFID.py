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
    return JSONResponse(content={"success": True, "message": "Demo mode: PN532 NFC Hat detected on I2C bus (addr=0x24), firmware v1.6"})

@router.post("/identify-rfid")
async def identify_rfid_post(request: Request):
    await asyncio.sleep(1.0)
    return JSONResponse(content={
        "success": True,
        "uid": "04:A1:B2:C3",
        "uid_length": 4,
        "type": ["MIFARE Classic 1K"],
        "sak": "08",
        "atqa": "00 04"
    })

@router.post("/write-uid")
async def write_uid_post(request: Request, write_request: WriteCardRequest):
    new_uid_hex = write_request.card_data.get("uid")
    if not new_uid_hex or len(new_uid_hex) != 8:
        return JSONResponse(content={"success": False, "error": "UID must be 8 hexadecimal characters"})
    await asyncio.sleep(1.0)
    formatted = ":".join(new_uid_hex[i:i+2] for i in range(0, 8, 2)).upper()
    return JSONResponse(content={"success": True, "message": f"Successfully wrote UID {formatted} to CUID card (Block 0 updated)"})

@router.post("/analyze")
async def analyze_rfid(request: Request):
    return JSONResponse(content={
        "success": True,
        "module": "Demo Security Analyzer",
        "issues": [
            {
                "type": "default_key",
                "risk": "HIGH",
                "recommendation": "Replace factory-default keys (FFFFFFFFFFFF / A0A1A2A3A4A5) with unique sector-specific keys immediately"
            },
            {
                "type": "static_uid",
                "risk": "MEDIUM",
                "recommendation": "4-byte static UIDs are cloneable; consider migrating to 7-byte UID cards or using challenge-response authentication"
            },
            {
                "type": "weak_authentication",
                "risk": "MEDIUM",
                "recommendation": "MIFARE Classic uses proprietary Crypto-1 cipher which is cryptographically broken; upgrade to MIFARE DESFire EV3 or equivalent"
            },
        ],
        "threat": {"score": 72, "status": "WARNING"}
    })
