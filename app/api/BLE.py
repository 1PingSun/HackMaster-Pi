from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.ble_service import BLEService
from services.real.ble_real import BLERealService

router = APIRouter(
    prefix="/BLE",
    tags=["BLE"]
)

templates = Jinja2Templates(directory="templates")


# ---------- Dependency ----------

def get_ble_service() -> BLEService:
    return BLERealService()


# ---------- HTML page routes ----------

@router.get("/beacon-scanner", response_class=HTMLResponse)
def read_beacon_scanner(request: Request):
    return templates.TemplateResponse(
        "BLE/beacon-scanner.html",
        {"request": request, "message": "Beacon Scanner"}
    )

@router.get("/beacon-storage", response_class=HTMLResponse)
def read_beacon_storage(request: Request):
    return templates.TemplateResponse(
        "BLE/beacon-storage.html",
        {"request": request, "message": "Beacon Storage"}
    )

@router.get("/beacon-emulator", response_class=HTMLResponse)
def read_beacon_emulator(request: Request):
    return templates.TemplateResponse(
        "BLE/beacon-emulator.html",
        {"request": request, "message": "Beacon Emulator"}
    )

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator_page(request: Request):
    return templates.TemplateResponse(
        "BLE/airpods-emulator.html",
        {"request": request, "message": "Wordlist Generator"}
    )


# ---------- API routes ----------

@router.get("/beacon-storage/profiles")
def get_profiles(service: BLEService = Depends(get_ble_service)):
    return service.get_profiles()

@router.post("/beacon-storage/profiles")
async def add_profile(profile: dict, service: BLEService = Depends(get_ble_service)):
    return await service.add_profile(profile)

@router.delete("/beacon-storage/profiles/{name}")
async def delete_profile(name: str, service: BLEService = Depends(get_ble_service)):
    return await service.delete_profile(name)

@router.post("/beacon-emulator/start")
async def start_beacon_emulator(data: dict, service: BLEService = Depends(get_ble_service)):
    result = await service.start_beacon_emulator(data.get("profile_name", ""))
    if result.get("success") == False:
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return result

@router.post("/beacon-emulator/stop")
async def stop_beacon_emulator(service: BLEService = Depends(get_ble_service)):
    return await service.stop_beacon_emulator()

@router.get("/beacon-emulator/status")
async def get_beacon_emulator_status(service: BLEService = Depends(get_ble_service)):
    return await service.get_beacon_emulator_status()

@router.post("/airpods-emulator/start")
async def start_airpods_scan(service: BLEService = Depends(get_ble_service)):
    return await service.start_airpods_emulator()

@router.post("/airpods-emulator/stop")
async def stop_airpods_scan(service: BLEService = Depends(get_ble_service)):
    return await service.stop_airpods_emulator()

@router.get("/airpods-emulator/status")
async def get_status(service: BLEService = Depends(get_ble_service)):
    return await service.get_airpods_emulator_status()

@router.get("/airpods-emulator/logs")
async def get_logs(service: BLEService = Depends(get_ble_service)):
    return await service.get_airpods_logs()
