import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api import WiFi, BLE, IR, RFID

DEMO_MODE = os.getenv("HACKMASTER_DEMO_MODE", "false").lower() == "true"

app = FastAPI(
    title="HackMaster Pi",
    description="An open source IoT Hacker Tool by using Raspberry Pi Zero 2 W",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(BLE.router)
app.include_router(WiFi.router)
app.include_router(IR.router)
app.include_router(RFID.router)

# Demo mode: override all dependencies with Mock services
if DEMO_MODE:
    from services.mock.wifi_mock import WiFiMockService
    from services.mock.ble_mock import BLEMockService
    from services.mock.ir_mock import IRMockService
    from services.mock.rfid_mock import RFIDMockService

    _wifi_mock = WiFiMockService()
    _ble_mock = BLEMockService()
    _ir_mock = IRMockService()
    _rfid_mock = RFIDMockService()

    app.dependency_overrides[WiFi.get_wifi_service] = lambda: _wifi_mock
    app.dependency_overrides[BLE.get_ble_service] = lambda: _ble_mock
    app.dependency_overrides[IR.get_ir_service] = lambda: _ir_mock
    app.dependency_overrides[RFID.get_rfid_service] = lambda: _rfid_mock


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "favicon.ico")
    return FileResponse(favicon_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
