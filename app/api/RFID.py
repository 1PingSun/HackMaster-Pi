import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List

from services.rfid_service import RFIDService
from services.real.rfid_real import RFIDRealService

router = APIRouter(
    prefix="/RFID",
    tags=["RFID"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ---------- Pydantic models ----------

class WriteCardRequest(BaseModel):
    card_data: Dict
    save_to_db: bool = False

class SaveCardsRequest(BaseModel):
    cards: List[Dict]
    filename: str


# ---------- Dependency ----------

def get_rfid_service() -> RFIDService:
    return RFIDRealService()


# ---------- HTML page routes ----------

@router.get("/identify-rfid", response_class=HTMLResponse)
def identify_rfid_page(request: Request):
    return templates.TemplateResponse(
        "RFID/identify-rfid.html",
        {"request": request, "message": "Identify RFID Card"}
    )

@router.get("/write-uid", response_class=HTMLResponse)
def write_uid_page(request: Request):
    return templates.TemplateResponse(
        "RFID/write-uid.html",
        {"request": request, "message": "Write UID to HF RFID CUID Card"}
    )


# ---------- API routes ----------

@router.post("/setup-pn532")
async def setup_pn532(service: RFIDService = Depends(get_rfid_service)):
    result = await service.setup_pn532()
    return JSONResponse(content=result)

@router.post("/identify-rfid")
async def identify_rfid_post(service: RFIDService = Depends(get_rfid_service)):
    result = await service.identify_rfid()
    return JSONResponse(content=result)

@router.post("/write-uid")
async def write_uid_post(write_request: WriteCardRequest, service: RFIDService = Depends(get_rfid_service)):
    result = await service.write_uid(write_request.card_data, write_request.save_to_db)
    return JSONResponse(content=result)

@router.post("/analyze")
async def analyze_rfid(request: Request, service: RFIDService = Depends(get_rfid_service)):
    data = await request.json()
    card_info = data.get("card_info", {})
    result = await service.analyze_rfid(card_info)
    return JSONResponse(content=result)
