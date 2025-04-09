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
    
    if running_process and running_process.poll() is None:
        return {"status": "already_running", "pid": running_process.pid}
    
    try:
        # 獲取當前工作目錄和腳本的絕對路徑
        cwd = os.getcwd()
        script_path = os.path.abspath("./mylib/apple_bleee/adv_airpods.py")
        
        # 確保腳本存在
        if not os.path.exists(script_path):
            return {"status": "error", "detail": f"Script not found at {script_path}"}
        
        # 使用 sudo 執行腳本，並添加 verbose 模式（如果腳本支持）
        cmd = ["sudo", "python3", script_path, "--verbose"]
        
        # 啟動進程
        with open("airpods_output.log", "w") as out_file, open("airpods_error.log", "w") as err_file:
            # 寫入一些調試信息
            out_file.write(f"Starting process with CWD: {cwd}\n")
            out_file.write(f"Command: {' '.join(cmd)}\n")
            out_file.write("--- Output below ---\n")
            
            process = subprocess.Popen(
                cmd,
                stdout=out_file,
                stderr=err_file,
                text=True,
                cwd=cwd  # 設置當前工作目錄
            )
        
        running_process = process
        return {
            "status": "started", 
            "pid": process.pid, 
            "cwd": cwd, 
            "script_path": script_path
        }
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
    
@router.get("/airpods-emulator/check")
async def check_process():
    global running_process
    
    if not running_process:
        return {"status": "not_initialized"}
    
    # 檢查進程是否存在
    try:
        # 檢查進程是否還在運行
        if running_process.poll() is None:
            # 檢查是否真的有這個進程
            try:
                proc = psutil.Process(running_process.pid)
                cmdline = ' '.join(proc.cmdline())
                return {
                    "status": "running", 
                    "pid": running_process.pid,
                    "cmdline": cmdline
                }
            except psutil.NoSuchProcess:
                return {"status": "process_not_found", "pid": running_process.pid}
        else:
            # 進程已結束，獲取返回碼
            return_code = running_process.returncode
            return {"status": "terminated", "return_code": return_code}
    except Exception as e:
        return {"status": "error", "error": str(e)}