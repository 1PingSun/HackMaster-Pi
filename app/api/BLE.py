from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import random

router = APIRouter(prefix="/BLE", tags=["BLE"])
templates = Jinja2Templates(directory="templates")

beacon_emulator_active = False
current_emulator_profile = None
airpods_running = False

mock_profiles = [
    {"name": "Lobby iBeacon",    "uuid": "E2C56DB5-DFFB-48D2-B060-D0F5A71096E0", "major": 1, "minor": 1, "power": -59},
    {"name": "Conference Room A","uuid": "5A4BCFCE-174E-4BAC-A814-092E77F6B7E5", "major": 2, "minor": 3, "power": -65},
    {"name": "Demo Beacon 1",    "uuid": "12345678-1234-1234-1234-123456789012", "major": 1, "minor": 1, "power": -59},
]

_BEACON_POOL = [
    {"uuid": "E2C56DB5-DFFB-48D2-B060-D0F5A71096E0", "name": "Lobby iBeacon"},
    {"uuid": "5A4BCFCE-174E-4BAC-A814-092E77F6B7E5", "name": "Conference Room A"},
    {"uuid": "74278BDA-B644-4520-8F0C-720EAF059935", "name": "Retail Display Beacon"},
    {"uuid": "B9407F30-F5F8-466E-AFF9-25556B57FE6D", "name": "Estimote Beacon #1"},
    {"uuid": "F7826DA6-4FA2-4E98-8024-BC5B71E0893E", "name": "Kontakt.io Beacon"},
    {"uuid": "ACFD065E-C3C0-11E3-9BBE-1A514932AC01", "name": "Museum Guide Beacon"},
    {"uuid": "D0D3FA86-CA76-45EC-9BD9-6AF4B9F3B02E", "name": "Airport Gate B12"},
    {"uuid": "3C5B26A8-F5B1-43D0-B23D-5C5F1E0E7F90", "name": "HackMaster Test Node"},
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
    global beacon_emulator_active, current_emulator_profile
    profile = next((p for p in mock_profiles if p["name"] == data.get("profile_name", "")), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    beacon_emulator_active = True
    current_emulator_profile = profile["name"]
    return {"status": "started", "profile": profile["name"]}

@router.post("/beacon-emulator/stop")
async def stop_beacon_emulator():
    global beacon_emulator_active, current_emulator_profile
    beacon_emulator_active = False
    current_emulator_profile = None
    return {"status": "stopped"}

@router.get("/beacon-emulator/status")
async def get_beacon_emulator_status():
    if beacon_emulator_active:
        return {"status": "running", "profile_name": current_emulator_profile}
    return {"status": "not_running", "profile_name": None}

@router.get("/beacon-scanner/scan")
async def scan_beacons():
    # Pick a random subset of beacons and assign realistic RSSI values
    count = random.randint(3, len(_BEACON_POOL))
    selected = random.sample(_BEACON_POOL, count)
    beacons = []
    for b in selected:
        beacons.append({
            "uuid": b["uuid"],
            "name": b["name"],
            "rssi": random.randint(-90, -35),
        })
    return {"beacons": beacons}

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
    return templates.TemplateResponse(request=request, name="BLE/airpods-emulator.html", context={"message": "Airpods Emulator"})

@router.post("/airpods-emulator/start")
async def start_airpods_scan():
    global airpods_running
    airpods_running = True
    return {"status": "started", "pid": 9823}

@router.post("/airpods-emulator/stop")
async def stop_airpods_scan():
    global airpods_running
    airpods_running = False
    return {"status": "stopped", "pid": 9823}

@router.get("/airpods-emulator/status")
async def get_status():
    return {"status": "running" if airpods_running else "not_running", "pid": 9823 if airpods_running else None}

@router.get("/airpods-emulator/logs")
async def get_logs():
    return {
        "output": (
            "[BLE] Advertising AirPods Pro (2nd Gen) proximity pair packet\n"
            "[BLE] Tx power: -59 dBm  |  Interval: 100 ms\n"
            "[BLE] Device detected: iPhone 15 Pro (rssi=-52)\n"
            "[BLE] Device detected: iPad Air 5 (rssi=-68)\n"
            "[BLE] Device detected: MacBook Pro M3 (rssi=-74)\n"
            "[BLE] Total triggers: 3"
        ),
        "errors": ""
    }
