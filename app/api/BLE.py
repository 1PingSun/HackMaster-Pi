from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import os
import signal
import psutil

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

@router.get("/airpods-emulator", response_class=HTMLResponse)
def read_airpods_emulator(request: Request):
    return templates.TemplateResponse(
        "BLE/airpods-emulator.html", 
        {"request": request, "message": "Wordlist Generator"}
    )

@router.post("/airpods-emulator/start")
async def start_airpods_scan():
    global running_process
    
    # 檢查是否已經在運行
    if running_process and running_process.poll() is None:
        return {"status": "already_running", "pid": running_process.pid}
    
    try:
        # 使用 pkexec 或 sudo 執行腳本
        # 注意：需要配置 sudoers 允許無密碼執行此特定腳本
        cmd = ["sudo", "python3", "./apple_bleee/adv_airpods.py"]
        
        # 啟動進程，不阻塞 API
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 儲存進程引用
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