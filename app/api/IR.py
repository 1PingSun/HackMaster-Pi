import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from services.ir_service import IRService
from services.real.ir_real import IRRealService

router = APIRouter(
    prefix="/IR",
    tags=["IR"]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ---------- Pydantic models ----------

class TransmitRequest(BaseModel):
    signalData: str
    format: Optional[str] = "RAW"


# ---------- Dependency ----------

def get_ir_service() -> IRService:
    return IRRealService()


# ---------- HTML page routes ----------

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


# ---------- API routes ----------

@router.post("/record")
async def record_ir_signal(service: IRService = Depends(get_ir_service)):
    return await service.start_recording()

@router.post("/record/cancel")
async def cancel_ir_recording(service: IRService = Depends(get_ir_service)):
    return await service.cancel_recording()

@router.get("/status")
async def get_ir_status(service: IRService = Depends(get_ir_service)):
    return await service.get_status()

@router.post("/transmit")
async def transmit_ir_signal(request: TransmitRequest, service: IRService = Depends(get_ir_service)):
    return await service.transmit(request.signalData, request.format)

@router.post("/enumerate")
async def enumerate_ir_code(data: dict, service: IRService = Depends(get_ir_service)):
    device_type = data.get("device_type", "")
    brand = data.get("brand", "")
    protocol = data.get("protocol", "all")
    function = data.get("function", "")
    code_index = data.get("code_index", 0)
    return await service.enumerate_code(device_type, brand, protocol, function, code_index)
