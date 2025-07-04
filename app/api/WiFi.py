from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import subprocess
import time
import uuid
import json
from .mylib.WeakPasswordGenerater.main import PasswordGenerator
from .mylib.ap_scan import scan_wifi_networks
import random
import asyncio
import csv
import glob
import re
from datetime import datetime

router = APIRouter(
    prefix="/WiFi",
    tags=["WiFi"]
)

templates = Jinja2Templates(directory="templates")

# AP 狀態變數
ap_running = False
ap_start_time = None
ap_config = None
capture_active = False
capture_process = None
capture_file = None
connected_clients = []

# 全域網卡名稱列表
network_adapters = []

# 定義 AP 配置模型
class APConfig(BaseModel):
    ssid: str
    security: str
    password: Optional[str] = ""
    channel: str
    hidden: bool = False
    captive_portal: bool = False
    internet_sharing: bool = False
    mac_address: Optional[str] = None

# 定義捕獲文件模型
class CaptureFile(BaseModel):
    id: str
    filename: str
    path: str
    size: int
    timestamp: str

# 儲存的捕獲文件
capture_files = []

# 定義請求模型
class ScanRequest(BaseModel):
    bands: Dict[str, bool]
    show_hidden: bool = False

# 定義網路介面請求模型
class NetworkInterfaceRequest(BaseModel):
    interface: str

# 定義掃描請求模型
class ScanWifiRequest(BaseModel):
    interface: str
    timeout: int = 10

# 定義監聽握手包請求模型
class CaptureRequest(BaseModel):
    interface: str
    bssid: str
    channel: int
    output_file: Optional[str] = None

# 定義斷線訊號請求模型
class DeauthRequest(BaseModel):
    interface: str
    bssid: str
    packets: int = 10  # 預設 10 個封包
    broadcast: bool = True

# 定義破解請求模型
class CrackRequest(BaseModel):
    capture_file: str
    wordlist: str
    hash_mode: Optional[str] = "2500"
    attack_mode: Optional[str] = "0"
    ssid: Optional[str] = None

# 定義請求模型
class WordlistRequest(BaseModel):
    output_filename: str
    info_data: Dict[str, List[str]]

# 定義頻道設定請求模型
class ChannelRequest(BaseModel):
    interface: str
    channel: str

@router.get("/ap-emulator", response_class=HTMLResponse)
def read_ap_emulator(request: Request):
    return templates.TemplateResponse(
        "WiFi/ap-emulator.html",
        {"request": request, "message": "AP Emulator"}
    )

@router.get("/wifi-scanner", response_class=HTMLResponse)
def read_wifi_scanner(request: Request):
    return templates.TemplateResponse(
        "WiFi/wifi-scanner.html",
        {"request": request, "message": "WiFi Scanner"}
    )

@router.get("/wifi-cracker", response_class=HTMLResponse)
def read_wifi_cracker(request: Request):
    return templates.TemplateResponse(
        "WiFi/wifi-cracker.html",
        {"request": request, "message": "Wi-Fi Password Cracker"}
    )

@router.get("/wordlist-generator", response_class=HTMLResponse)
def read_wordlist_generator(request: Request):
    return templates.TemplateResponse(
        "WiFi/wordlist-generator.html",
        {"request": request, "message": "Wordlist Generator"}
    )

@router.get("/interface/details")
async def list_adapters(request: Request):
    """
    執行 ifconfig -a 命令並返回所有網路介面的詳細資訊
    """
    global network_adapters
    
    try:
        # 執行 ifconfig -a 命令
        result = subprocess.run(
            ["ifconfig", "-a"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            # 截取網卡名稱
            network_adapters = extract_adapter_names(result.stdout)
            
            return {
                "success": True,
                "output": result.stdout,
                "message": "Network adapters listed successfully",
                "adapters": network_adapters
            }
        else:
            return {
                "success": False,
                "message": f"Failed to execute ifconfig: {result.stderr}",
                "output": result.stderr,
                "adapters": []
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Command timed out",
            "output": "",
            "adapters": []
        }
    except FileNotFoundError:
        return {
            "success": False,
            "message": "ifconfig command not found. Please ensure net-tools is installed.",
            "output": "",
            "adapters": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error executing ifconfig: {str(e)}",
            "output": "",
            "adapters": []
        }

def extract_adapter_names(ifconfig_output):
    """
    從 ifconfig 輸出中截取網卡名稱
    """
    adapter_names = []
    lines = ifconfig_output.split('\n')
    
    for line in lines:
        # 網卡名稱通常在行的開頭，後面跟著冒號或空格
        # 例如: "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500"
        # 或: "wlan0     Link encap:Ethernet  HWaddr"
        if line and not line.startswith(' ') and not line.startswith('\t'):
            # 提取網卡名稱 (在冒號或空格之前)
            if ':' in line:
                adapter_name = line.split(':')[0].strip()
            else:
                # 處理某些系統中沒有冒號的情況
                parts = line.split()
                if parts:
                    adapter_name = parts[0].strip()
                else:
                    continue
            
            # 過濾掉空字串和無效名稱
            if adapter_name and adapter_name.isalnum() or any(c in adapter_name for c in ['-', '_']):
                adapter_names.append(adapter_name)
    
    return adapter_names

@router.get("/interface/list")
async def get_adapter_names():
    """
    返回已截取的網卡名稱列表
    """
    global network_adapters
    
    return {
        "success": True,
        "adapters": network_adapters,
        "count": len(network_adapters)
    }

@router.post("/interface/monitorMode")
async def activate_monitor_mode(request: NetworkInterfaceRequest):
    """
    啟用指定網路介面的監聽模式
    """
    try:
        # 執行 sudo ifconfig {interface_name} up
        up_result = subprocess.run(
            ["sudo", "ifconfig", request.interface, "up"],
            capture_output=True, text=True, timeout=10
        )
        
        if up_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to bring up interface {request.interface}",
                "error": up_result.stderr
            }
        
        # 執行 sudo iwconfig {interface_name} mode monitor
        monitor_result = subprocess.run(
            ["sudo", "iwconfig", request.interface, "mode", "monitor"],
            capture_output=True, text=True, timeout=10
        )
        
        if monitor_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to set monitor mode for {request.interface}",
                "error": monitor_result.stderr
            }
        
        return {
            "success": True,
            "message": f"Monitor mode activated successfully for {request.interface}",
            "interface": request.interface
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Command timed out",
            "interface": request.interface
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error activating monitor mode: {str(e)}",
            "interface": request.interface
        }

@router.get("/interface/status")
async def get_interface_status(interface: str):
    """
    取得指定網路介面的狀態，特別是其模式
    """
    try:
        # 執行 iwconfig 命令
        result = subprocess.run(
            ["iwconfig", interface],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to get status for interface {interface}",
                "error": result.stderr,
                "interface": interface
            }
        
        output = result.stdout
        mode = "Unknown"
        
        # 從 iwconfig 輸出中擷取模式
        if "Mode:Monitor" in output:
            mode = "Monitor"
        elif "Mode:Managed" in output:
            mode = "Managed"
        elif "Mode:Master" in output:
            mode = "Master"
        elif "Mode:Ad-Hoc" in output:
            mode = "Ad-Hoc"
        elif "no wireless extensions" in output.lower():
            return {
                "success": False,
                "message": f"Interface {interface} is not a wireless interface",
                "interface": interface
            }
        
        return {
            "success": True,
            "interface": interface,
            "mode": mode,
            "status": f"{mode} mode",
            "output": output
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Command timed out",
            "interface": interface
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting interface status: {str(e)}",
            "interface": interface
        }

@router.post("/ap/scan")
async def scan_wifi(request: ScanWifiRequest):
    try:
        # 使用 asyncio 在執行緒池中運行掃描，避免阻塞事件循環
        loop = asyncio.get_event_loop()
        nearby_ap = await loop.run_in_executor(
            None, 
            scan_wifi_networks, 
            request.interface, 
            request.timeout
        )
        
        return {
            "success": True,
            "ap_list": nearby_ap,
            "interface": request.interface,
            "count": len(nearby_ap)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to scan networks: {str(e)}",
            "ap_list": [],
            "interface": request.interface,
            "count": 0
        }
    
@router.post('/interface/channel')
async def set_interface_channel(request: ChannelRequest):
    """
    設定指定網路介面的頻道
    """
    try:
        # 執行 sudo iwconfig {interface_name} channel {channel}
        result = subprocess.run(
            ["sudo", "iwconfig", request.interface, "channel", request.channel],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to set channel {request.channel} for {request.interface}",
                "error": result.stderr
            }
        
        return {
            "success": True,
            "message": f"Channel {request.channel} set successfully for {request.interface}",
            "interface": request.interface,
            "channel": request.channel
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Command timed out",
            "interface": request.interface,
            "channel": request.channel
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error setting channel: {str(e)}",
            "interface": request.interface,
            "channel": request.channel
        }

@router.post("/capture/start")
async def start_capture(request: CaptureRequest, background_tasks: BackgroundTasks):
    """
    開始捕獲 Wi-Fi 流量
    """
    global capture_active, capture_process
    
    if capture_active:
        return {
            "success": False,
            "message": "Capture is already running"
        }
    
    try:
        # 使用固定的輸出文件名
        output_file = "capture"
            
        # 確保捕獲目錄存在
        os.makedirs("data/captures", exist_ok=True)
        output_path = os.path.join("data/captures", output_file)
        
        # 刪除舊的捕獲文件（如果存在）
        old_files = [
            f"{output_path}.cap",
            f"{output_path}-01.cap",
            f"{output_path}-01.csv",
            f"{output_path}-01.kismet.csv",
            f"{output_path}-01.log.csv"
        ]
        
        for old_file in old_files:
            try:
                if os.path.exists(old_file):
                    os.remove(old_file)
                    print(f"Removed old capture file: {old_file}")
            except Exception as e:
                print(f"Failed to remove old file {old_file}: {e}")
        
        # 使用 airodump-ng 開始捕獲流量
        # 指令範例：sudo airodump-ng -c 7 --bssid BO:BE:76:CD:97:24 -w capture wlan1
        capture_command = [
            "sudo", "airodump-ng",
            "-c", str(request.channel),
            "--bssid", request.bssid,
            "-w", output_path,
            request.interface
        ]
        
        # 在背景啟動捕獲進程
        background_tasks.add_task(run_capture_process, capture_command, output_path)
        
        return {
            "success": True,
            "message": "Traffic capture started",
            "capture_file": "capture.cap",
            "command": " ".join(capture_command)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to start capture: {str(e)}"
        }

@router.post("/deauth/send")
async def send_deauth(request: DeauthRequest):
    """
    發送解除認證封包
    """
    try:
        # 構建 aireplay-ng 指令
        # sudo aireplay-ng --deauth {packets} -a {bssid} {interface}
        deauth_command = [
            "sudo", "aireplay-ng",
            "--deauth", str(request.packets),
            "-a", request.bssid,
            request.interface
        ]
        
        # 如果不是廣播模式，可以加入特定客戶端MAC
        # 這裡暫時只支援廣播模式（對所有連接的客戶端發送）
        
        # 執行指令
        result = subprocess.run(
            deauth_command,
            capture_output=True, 
            text=True, 
            timeout=30  # 30秒超時
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Successfully sent {request.packets} deauth packets to {request.bssid}",
                "packets_sent": request.packets,
                "target_bssid": request.bssid,
                "interface": request.interface,
                "command": " ".join(deauth_command),
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send deauth packets: {result.stderr}",
                "command": " ".join(deauth_command),
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "Deauth command timed out (30 seconds)",
            "packets_sent": 0
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending deauth packets: {str(e)}",
            "packets_sent": 0
        }


@router.post("/capture/stop")
async def stop_capture():
    """
    停止捕獲 Wi-Fi 流量
    """
    global capture_active, capture_process
    
    try:
        if not capture_active or not capture_process:
            return {
                "success": False,
                "message": "No capture is currently running"
            }
        
        # 終止捕獲進程 (asyncio 子進程)
        capture_process.terminate()
        
        # 等待進程結束
        try:
            await asyncio.wait_for(capture_process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            capture_process.kill()
            await capture_process.wait()
        
        capture_active = False
        capture_process = None
        
        return {
            "success": True,
            "message": "Traffic capture stopped"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to stop capture: {str(e)}"
        }

# 背景捕獲進程
async def run_capture_process(command, output_path):
    global capture_process, capture_active
    
    try:
        capture_active = True
        
        # 使用 asyncio.create_subprocess_exec 創建異步子進程
        capture_process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 異步等待進程完成或被終止
        await capture_process.wait()
        
    except Exception as e:
        print(f"Capture process error: {e}")
    finally:
        capture_active = False
        capture_process = None

@router.post("/wordlist-generator")
async def generate_wordlist(request: WordlistRequest):
    try:
        # 確保檔案名稱合法
        filename = request.output_filename
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        # 建立生成器實例
        generator = PasswordGenerator(output_file=f"static/wordlists/{filename}")
        
        # 從請求中取得資料
        info_data = request.info_data
        
        # 生成密碼字典
        generator.generate(
            DATE=info_data.get('date', []),
            TEL=info_data.get('tel', []),
            NAME=info_data.get('name', []),
            ID=info_data.get('ID', []),
            SSID=info_data.get('SSID', [''])[0] if info_data.get('SSID') else ''
        )
        
        # 讀取生成的檔案以取得樣本和行數
        file_path = f"static/wordlists/{filename}"
        with open(file_path, 'r') as f:
            lines = f.readlines()
            total_count = len(lines)
            sample = ''.join(lines[:10]) # 只回傳前10行作為樣本
            
        return JSONResponse({
            "success": True,
            "filename": filename,
            "count": total_count,
            "sample": sample,
            "download_link": f"/static/wordlists/{filename}"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })