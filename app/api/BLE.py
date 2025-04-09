from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import os
import signal
import psutil
from .mylib.beacon import beacon_emulator
import json
from pathlib import Path

PROFILES_FILE = Path("data/beacon_profiles.json")
PROFILES_FILE.parent.mkdir(exist_ok=True)

# 確保設定檔檔案存在
if not PROFILES_FILE.exists():
    PROFILES_FILE.write_text("[]")

router = APIRouter(
    prefix="/BLE",
    tags=["BLE"]
)

running_process = None

templates = Jinja2Templates(directory="templates")

@router.get("/beacon-scanner", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
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

@router.get("/beacon-storage/profiles")
def get_profiles():
    profiles = json.loads(PROFILES_FILE.read_text())
    return profiles

@router.post("/beacon-storage/profiles")
async def add_profile(profile: dict):
    profiles = json.loads(PROFILES_FILE.read_text())
    profiles.append(profile)
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2))
    return {"status": "success"}

@router.delete("/beacon-storage/profiles/{name}")
async def delete_profile(name: str):
    profiles = json.loads(PROFILES_FILE.read_text())
    profiles = [p for p in profiles if p["name"] != name]
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2))
    return {"status": "success"}

@router.get("/beacon-emulator", response_class=HTMLResponse)
def read_beacon_emulator(request: Request):
    return templates.TemplateResponse(
        "BLE/beacon-emulator.html", 
        {"request": request, "message": "Beacon Emulator"}
    )

@router.get("/beacon-emulator/start")
async def start_beacon_emulator():
    profiles = json.loads(PROFILES_FILE.read_text())
    profile = next((p for p in profiles if p["name"] == data["profile_name"]), None)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    beacon_emulator.start_ibeacon(
        uuid=profile["uuid"],
        major=profile["major"],
        minor=profile["minor"],
        power=profile["power"]
    )
    return {"status": "started"}

@router.get("/beacon-emulator/stop")
async def stop_beacon_emulator():
    beacon_emulator.stop_ibeacon()
    return {"status": "stopped"}

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
    return templates.TemplateResponse(
        "BLE/airpods-emulator.html", 
        {"request": request, "message": "Wordlist Generator"}
    )

@router.post("/airpods-emulator/start")
async def start_airpods_scan():
    global running_process
    
    if running_process and running_process.poll() is None:
        return {"status": "already_running", "pid": running_process.pid}
    
    try:
        # 獲取當前環境變數
        env = os.environ.copy()
        
        # 使用 sudo -E 保留環境變數
        cmd = ["sudo", "-E", "python3", "api/mylib/apple_bleee/adv_airpods.py"]
        
        # 啟動進程
        with open("airpods_output.log", "w") as out_file, open("airpods_error.log", "w") as err_file:
            process = subprocess.Popen(
                cmd,
                stdout=out_file,
                stderr=err_file,
                text=True,
                env=env,
                preexec_fn=os.setsid
            )
        
        running_process = process
        return {"status": "started", "pid": process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")

@router.post("/airpods-emulator/stop")
async def stop_airpods_scan():
    global running_process
    
    if not running_process:
        return {"status": "not_running"}
    
    try:
        # 獲取進程 PID
        pid = running_process.pid
        
        # 終止主進程及其子進程
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        for child in children:
            child.terminate()
        
        # 終止主進程
        parent.terminate()
        
        # 確保進程已終止
        gone, alive = psutil.wait_procs([parent], timeout=3)
        for p in alive:
            p.kill()
        
        running_process = None
        return {"status": "stopped", "pid": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")

@router.get("/airpods-emulator/status")
async def get_status():
    global running_process
    
    if running_process and running_process.poll() is None:
        return {"status": "running", "pid": running_process.pid}
    else:
        return {"status": "not_running"}
    
@router.get("/airpods-emulator/logs")
async def get_logs():
    try:
        error_content = ""
        output_content = ""
        
        if os.path.exists("airpods_error.log"):
            with open("airpods_error.log", "r") as error_file:
                error_content = error_file.read()
                
        if os.path.exists("airpods_output.log"):
            with open("airpods_output.log", "r") as output_file:
                output_content = output_file.read()
                
        return {"output": output_content, "errors": error_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")