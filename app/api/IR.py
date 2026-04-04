from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import asyncio

router = APIRouter(prefix="/IR", tags=["IR"])
templates = Jinja2Templates(directory="templates")

ir_recording = False
ir_signal = None

class TransmitRequest(BaseModel):
    signalData: str
    format: Optional[str] = "RAW"

@router.get("/signal-learner", response_class=HTMLResponse)
def read_signal_learner(request: Request):
    return templates.TemplateResponse(request=request, name="IR/signal-learner.html", context={"message": "IR Signal Learner"})

@router.get("/signal-enumerator", response_class=HTMLResponse)
def read_signal_enumerator(request: Request):
    return templates.TemplateResponse(request=request, name="IR/signal-enumerator.html", context={"message": "IR Signal Enumerator"})

@router.post("/record")
async def record_ir_signal():
    global ir_recording, ir_signal
    if ir_recording:
        return {"success": False, "message": "Already recording"}
    ir_recording = True
    ir_signal = None
    
    async def mock_receive():
        global ir_recording, ir_signal
        await asyncio.sleep(2)
        if ir_recording:
            ir_signal = {"data": "01010101DEMO1234", "format": "NEC", "length": 32}
            ir_recording = False
            
    asyncio.create_task(mock_receive())
    return {"success": True, "message": "IR recording started"}

@router.post("/record/cancel")
async def cancel_ir_recording():
    global ir_recording, ir_signal
    ir_recording = False
    ir_signal = None
    return {"success": True, "message": "Recording cancelled"}

@router.get("/status")
async def get_ir_status():
    if ir_recording:
        return {"status": "recording"}
    elif ir_signal:
        return {"status": "completed", "signal": ir_signal}
    else:
        return {"status": "idle"}

@router.post("/transmit")
async def transmit_ir_signal(request: TransmitRequest):
    await asyncio.sleep(0.5)
    return {"success": True, "message": "Signal transmitted successfully (DEMO)"}

@router.post("/enumerate")
async def enumerate_ir_code(data: dict):
    code_index = data.get("code_index", 0)
    await asyncio.sleep(0.1)
    return {
        "success": True,
        "code_index": code_index,
        "code_hex": "A1B2C3D4",
        "protocol": data.get("protocol", "NEC"),
        "response": True,
        "bits": 32
    }
