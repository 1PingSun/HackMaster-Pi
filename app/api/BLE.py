from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/BLE",
    tags=["BLE"]
)

templates = Jinja2Templates(directory="templates")

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
    return templates.TemplateResponse(
        "BLE/airpods-emulator.html", 
        {"request": request, "message": "Wordlist Generator"}
    )