from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/BLE", tags=["BLE"])
templates = Jinja2Templates(directory="templates")

beacon_emulator_active = False
airpods_running = False

mock_profiles = [
    {"name": "Demo Beacon 1", "uuid": "12345678-1234-1234-1234-123456789012", "major": 1, "minor": 1, "power": -59}
]

@router.get("/beacon-scanner", response_class=HTMLResponse)
def read_beacon_scanner(request: Request):
    return templates.TemplateResponse(request=request, name="BLE/beacon-scanner.html", context={"message": "Beacon Scanner"})

@router.get("/beacon-storage", response_class=HTMLResponse)
def read_beacon_storage(request: Request):
    return templates.TemplateResponse(request=request, name="BLE/beacon-storage.html", context={"message": "Beacon Storage"})

@router.get("/beacon-storage/profiles")
def get_profiles():
    return mock_profiles

@router.post("/beacon-storage/profiles")
async def add_profile(profile: dict):
    mock_profiles.append(profile)
    return {"status": "success"}

@router.delete("/beacon-storage/profiles/{name}")
async def delete_profile(name: str):
    global mock_profiles
    mock_profiles = [p for p in mock_profiles if p["name"] != name]
    return {"status": "success"}

@router.get("/beacon-emulator", response_class=HTMLResponse)
def read_beacon_emulator(request: Request):
    return templates.TemplateResponse(request=request, name="BLE/beacon-emulator.html", context={"message": "Beacon Emulator"})

@router.post("/beacon-emulator/start")
async def start_beacon_emulator(data: dict):
    global beacon_emulator_active
    profile = next((p for p in mock_profiles if p["name"] == data.get("profile_name", "")), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    beacon_emulator_active = True
    return {"status": "started", "profile": profile["name"]}

@router.post("/beacon-emulator/stop")
async def stop_beacon_emulator():
    global beacon_emulator_active
    beacon_emulator_active = False
    return {"status": "stopped"}

@router.get("/beacon-emulator/status")
async def get_beacon_emulator_status():
    return {"status": "running" if beacon_emulator_active else "not_running"}

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
    return templates.TemplateResponse(request=request, name="BLE/airpods-emulator.html", context={"message": "Airpods Emulator"})

@router.post("/airpods-emulator/start")
async def start_airpods_scan():
    global airpods_running
    airpods_running = True
    return {"status": "started", "pid": 9999}

@router.post("/airpods-emulator/stop")
async def stop_airpods_scan():
    global airpods_running
    airpods_running = False
    return {"status": "stopped", "pid": 9999}

@router.get("/airpods-emulator/status")
async def get_status():
    return {"status": "running" if airpods_running else "not_running", "pid": 9999 if airpods_running else None}

@router.get("/airpods-emulator/logs")
async def get_logs():
    return {"output": "Mock AirPods scan output in demo mode...\nDevices found: 3", "errors": ""}
