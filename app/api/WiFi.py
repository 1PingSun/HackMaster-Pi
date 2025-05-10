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
import random
import asyncio
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
    packets: int = 5
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

@router.post("/ap/start")
async def start_ap(config: APConfig):
    global ap_running, ap_start_time, ap_config
    
    if ap_running:
        return {"success": False, "message": "AP is already running"}
    
    try:
        # 這裡實現啟動 AP 的代碼
        # 在 Raspberry Pi 上，這可能涉及設置 hostapd 和 dnsmasq
        
        # 模擬啟動延遲
        await asyncio.sleep(2)
        
        # 更新狀態
        ap_running = True
        ap_start_time = datetime.now()
        ap_config = config.dict()
        
        return {"success": True, "message": "Access point started successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/ap/stop")
async def stop_ap():
    global ap_running, ap_start_time, ap_config, capture_active
    
    if not ap_running:
        return {"success": False, "message": "No AP is currently running"}
    
    try:
        # 如果有正在進行的捕獲，停止它
        if capture_active:
            await stop_capture()
        
        # 這裡實現停止 AP 的代碼
        # 在 Raspberry Pi 上，這可能涉及停止 hostapd 和 dnsmasq 服務
        
        # 模擬停止延遲
        await asyncio.sleep(1)
        
        # 更新狀態
        ap_running = False
        ap_start_time = None
        ap_config = None
        connected_clients = []
        
        return {"success": True, "message": "Access point stopped successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/ap/status")
async def get_ap_status():
    global ap_running, ap_start_time, ap_config, capture_active, connected_clients
    
    if not ap_running:
        return {"success": False, "message": "No AP is currently running"}
    
    try:
        # 在實際應用中，這裡應該檢查實際連接的客戶端
        # 這裡我們使用模擬數據
        
        # 模擬更新已連接的客戶端
        update_connected_clients()
        
        uptime = int((datetime.now() - ap_start_time).total_seconds())
        
        return {
            "success": True,
            "running": ap_running,
            "uptime": uptime,
            "config": ap_config,
            "capture_active": capture_active,
            "connected_clients": connected_clients
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/ap/capture/start")
async def start_capture():
    global ap_running, capture_active, capture_process, capture_file
    
    if not ap_running:
        return {"success": False, "message": "No AP is currently running"}
    
    if capture_active:
        return {"success": False, "message": "Capture is already running"}
    
    try:
        # 生成捕獲文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ap_capture_{timestamp}.pcap"
        
        # 確保捕獲目錄存在
        os.makedirs("data/captures", exist_ok=True)
        
        capture_path = os.path.join("data/captures", filename)
        
        # 在實際應用中，這裡應該啟動 tcpdump 或類似工具
        # 模擬捕獲進程
        # capture_process = subprocess.Popen(
        #     ["tcpdump", "-i", "wlan0", "-w", capture_path],
        #     stdout=subprocess.PIPE, stderr=subprocess.PIPE
        # )
        
        # 更新狀態
        capture_active = True
        capture_file = {
            "path": capture_path,
            "filename": filename
        }
        
        return {"success": True, "message": "Packet capture started"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/ap/capture/stop")
async def stop_capture():
    global capture_active, capture_process, capture_file, capture_files
    
    if not capture_active:
        return {"success": False, "message": "No capture is currently running"}
    
    try:
        # 在實際應用中，這裡應該停止 tcpdump 進程
        # if capture_process:
        #     capture_process.terminate()
        #     capture_process.wait()
        
        # 模擬捕獲延遲
        await asyncio.sleep(1)
        
        # 更新狀態
        capture_active = False
        
        # 在實際應用中，這將是真實的文件大小
        file_size = 1024 * 1024 * (0.1 + 0.9 * random.random())  # 模擬 0.1-1 MB 的文件
        
        # 添加捕獲文件到列表
        capture_id = str(uuid.uuid4())
        capture_entry = {
            "id": capture_id,
            "filename": capture_file["filename"],
            "path": capture_file["path"],
            "size": file_size,
            "timestamp": datetime.now().isoformat()
        }
        
        capture_files.append(capture_entry)
        
        # 保存捕獲文件列表到持久存儲
        save_capture_files()
        
        result = {
            "success": True,
            "message": "Packet capture stopped",
            "capture_file": capture_entry
        }
        
        capture_process = None
        capture_file = None
        
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/ap/capture/list")
async def list_captures():
    global capture_files
    
    try:
        # 載入捕獲文件列表（如果尚未載入）
        if not capture_files:
            load_capture_files()
        
        return {"success": True, "captures": capture_files}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/ap/capture/download/{capture_id}")
async def download_capture(capture_id: str):
    global capture_files
    
    try:
        # 載入捕獲文件列表（如果尚未載入）
        if not capture_files:
            load_capture_files()
        
        # 查找指定的捕獲文件
        capture = next((c for c in capture_files if c["id"] == capture_id), None)
        
        if not capture:
            raise HTTPException(status_code=404, detail="Capture file not found")
        
        # 在實際應用中，這將返回真實的文件
        # 現在我們返回一個模擬文件
        # return FileResponse(
        #     capture["path"],
        #     filename=capture["filename"],
        #     media_type="application/vnd.tcpdump.pcap"
        # )
        
        # 為演示創建示例 pcap 文件
        dummy_path = create_dummy_pcap(capture["filename"])
        
        return FileResponse(
            dummy_path,
            filename=capture["filename"],
            media_type="application/vnd.tcpdump.pcap"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 工具函數：更新連接的客戶端
def update_connected_clients():
    global connected_clients
    
    # 在實際應用中，這將從系統獲取實際連接的客戶端
    # 這裡我們使用模擬數據
    
    # 隨機決定是否更改客戶端列表
    if random.random() < 0.3:  # 30% 的機率更新
        # 生成隨機數量的客戶端
        num_clients = random.randint(0, 3)
        connected_clients = []
        
        for i in range(num_clients):
            # 生成隨機 MAC 地址
            mac = ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
            
            # 生成隨機 IP 地址
            ip = f"192.168.4.{random.randint(2, 20)}"
            
            # 隨機設備名稱
            devices = ["iPhone", "Android", "iPad", "MacBook", "Windows-PC", "Unknown"]
            hostname = f"{random.choice(devices)}-{random.randint(1, 999)}"
            
            # 隨機連接時間
            connected_time = f"{random.randint(1, 59)} minutes"
            
            client = {
                "mac": mac,
                "ip": ip,
                "hostname": hostname,
                "connected_time": connected_time
            }
            
            connected_clients.append(client)

# 工具函數：保存捕獲文件列表
def save_capture_files():
    global capture_files
    
    try:
        # 確保目錄存在
        os.makedirs("data", exist_ok=True)
        
        # 保存到文件
        with open("data/capture_files.json", "w") as f:
            json.dump(capture_files, f)
    except Exception as e:
        print(f"Error saving capture files: {e}")

# 工具函數：載入捕獲文件列表
def load_capture_files():
    global capture_files
    
    try:
        # 檢查文件是否存在
        if os.path.exists("data/capture_files.json"):
            with open("data/capture_files.json", "r") as f:
                capture_files = json.load(f)
        else:
            capture_files = []
    except Exception as e:
        print(f"Error loading capture files: {e}")
        capture_files = []

# 工具函數：創建模擬 pcap 文件
def create_dummy_pcap(filename):
    # 創建一個簡單的二進制文件作為 pcap 
    dummy_path = os.path.join("data/captures", filename)
    os.makedirs(os.path.dirname(dummy_path), exist_ok=True)
    
    with open(dummy_path, "wb") as f:
        # 寫入 pcap 文件頭
        f.write(bytes.fromhex("d4c3b2a1020004000000000000000000ffff000001000000"))
        # 添加一些隨機數據
        for _ in range(1000):
            f.write(os.urandom(16))
    
    return dummy_path

@router.post("/scan")
async def scan_networks(config: ScanRequest):
    """
    掃描周圍的 WiFi 網路
    """
    try:
        # 在 Raspberry Pi 上，這應該使用 iwlist 或 iw 命令來掃描網路
        # 這裡我們使用模擬數據進行演示
        
        # 模擬掃描延遲
        await asyncio.sleep(3)
        
        # 檢查啟用的頻段
        enabled_bands = []
        if config.bands.get("2.4GHz", False):
            enabled_bands.append("2.4GHz")
        if config.bands.get("5GHz", False):
            enabled_bands.append("5GHz")
        if config.bands.get("6GHz", False):
            enabled_bands.append("6GHz")
        
        # 生成模擬網路列表
        networks = generate_mock_networks(config.show_hidden, enabled_bands)
        
        return {"success": True, "networks": networks}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 工具函數：生成模擬網路數據
def generate_mock_networks(include_hidden=False, bands=["2.4GHz", "5GHz"]):
    # 常見 WiFi 網路名稱
    common_ssids = [
        "WiFi-Home", "TP-LINK_58A92C", "ASUS_Router", "Netgear75", "HUAWEI-B535-95DA",
        "AndroidAP", "iPhone12", "ATT-WIFI-2854", "DIRECT-roku-724", "FRITZ!Box 7590",
        "Xiaomi_23A7_5G", "SKY-F5DE", "Virgin-Media-AC", "BTHub6-95MC", "Livebox-78FC",
        "eduroam", "Vodafone-WiFi", "FreeWifi", "WiFi-Cafe", "GuestWiFi",
        "UPC Wi-Free", "XFINITY", "TELUS", "Shaw Open", "Public WiFi"
    ]
    
    # 安全協議
    security_types = [
        "WPA2-PSK", "WPA2-PSK/WPA3-PSK", "WPA3-PSK", "WPA2-Enterprise", 
        "WPA2-PSK/CCMP", "Open", "WEP", "WPA-PSK/TKIP"
    ]
    
    # 生成廠商前綴
    vendor_prefixes = {
        "00:11:22": "Cisco", "aa:bb:cc": "Netgear", "e8:3a:12": "TP-Link",
        "5c:96:9d": "Apple", "f8:e9:4e": "D-Link", "ec:8a:c7": "Huawei",
        "fc:d7:33": "Google", "38:10:d5": "Samsung", "d4:6e:0e": "Xiaomi",
        "00:24:d4": "Ubiquiti", "c8:3a:35": "Tenda", "50:c7:bf": "TP-Link",
        "24:4c:e3": "Amazon", "70:5d:cc": "Microsoft", "00:50:56": "VMware"
    }
    
    # 生成隨機數量的網路
    num_networks = random.randint(5, 15)
    networks = []
    
    # 2.4GHz 頻道
    channels_2g = list(range(1, 14))
    # 5GHz 頻道
    channels_5g = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
    # 6GHz 頻道 (WiFi 6E)
    channels_6g = [1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93]
    
    # 生成網路
    for i in range(num_networks):
        # 決定頻段
        if not bands:
            band = "2.4GHz"
        else:
            band = random.choice(bands)
        
        # 頻率和頻道取決於頻段
        if band == "2.4GHz":
            channel = random.choice(channels_2g)
            frequency = 2412 + (channel - 1) * 5  # 2.4GHz 頻道頻率計算
            width = random.choice([20, 40])
        elif band == "5GHz":
            channel = random.choice(channels_5g)
            if channel < 100:
                frequency = 5180 + (channel - 36) * 5  # 5GHz 低頻道頻率計算
            else:
                frequency = 5500 + (channel - 100) * 5  # 5GHz 高頻道頻率計算
            width = random.choice([20, 40, 80, 160])
        else:  # 6GHz
            channel = random.choice(channels_6g)
            frequency = 5945 + channel * 5  # 6GHz 頻道頻率計算
            width = random.choice([20, 40, 80, 160, 320])
        
        # 生成隨機 MAC 地址
        mac_prefix = random.choice(list(vendor_prefixes.keys()))
        mac_suffix = ':'.join(['%02x' % random.randint(0, 255) for _ in range(3)])
        bssid = f"{mac_prefix}:{mac_suffix}"
        vendor = vendor_prefixes.get(mac_prefix, "Unknown")
        
        # 決定是否隱藏 SSID
        hidden = random.random() < 0.15  # 15% 的隱藏網絡概率
        
        # 如果網絡隱藏且不顯示隱藏網絡，跳過此網絡
        if hidden and not include_hidden:
            continue
        
        # 選擇 SSID
        if hidden:
            ssid = "<hidden>"
        else:
            ssid = random.choice(common_ssids)
            # 添加頻段識別
            if band == "5GHz" and random.random() < 0.7:
                ssid += "_5G"
            elif band == "6GHz" and random.random() < 0.9:
                ssid += "_6G"
            # 有時添加隨機後綴
            if random.random() < 0.3:
                ssid += f"-{random.randint(100, 999)}"
        
        # 選擇安全類型
        security_weights = [0.5, 0.25, 0.1, 0.05, 0.05, 0.03, 0.01, 0.01]  # 根據常見性加權
        security = random.choices(security_types, weights=security_weights)[0]
        
        # 生成信號強度 (dBm)
        signal_strength = -1 * random.randint(30, 95)  # 典型值在 -30 到 -95 dBm 之間
        
        # 生成第一次和最後一次看到的時間
        now = datetime.now()
        minutes_ago = random.randint(1, 60)
        last_seen = "Just now"
        first_seen = f"{minutes_ago} minutes ago"
        
        # 創建網絡對象
        network = {
            "ssid": ssid,
            "bssid": bssid,
            "signal_strength": signal_strength,
            "security": security,
            "channel": channel,
            "frequency": frequency,
            "width": width,
            "hidden": hidden,
            "vendor": vendor,
            "first_seen": first_seen,
            "last_seen": last_seen
        }
        
        networks.append(network)
    
    # 按信號強度排序（從強到弱）
    networks.sort(key=lambda x: x["signal_strength"], reverse=True)
    
    return networks

# 獲取可用網路介面
@router.get("/interfaces")
async def get_interfaces():
    try:
        # In a real environment, this would call system commands to get network interfaces
        # On Raspberry Pi, might use subprocess to execute iwconfig or ip link commands
        
        # Mock data
        interfaces = [
            {"name": "wlan0", "description": "Built-in Wi-Fi Adapter"},
            {"name": "wlan1", "description": "External USB Adapter"}
        ]
        
        return {"success": True, "interfaces": interfaces}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 啟動監聽模式
@router.post("/monitor/start")
async def start_monitor_mode(request: NetworkInterfaceRequest):
    try:
        # In a real environment, this would call system commands to set monitor mode
        # For example: airmon-ng start <interface>
        
        # Simulate operation delay
        await asyncio.sleep(2)
        
        monitor_interface = f"{request.interface}mon"
        
        return {
            "success": True, 
            "message": f"Monitor mode started successfully",
            "monitor_interface": monitor_interface
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# 掃描 Wi-Fi 網路
@router.post("/wifi/scan")
async def scan_wifi_networks(request: ScanWifiRequest):
    try:
        # In a real environment, this would call system commands to scan networks
        # For example: airodump-ng <interface> or iwlist <interface> scan
        
        # Simulate scanning delay
        await asyncio.sleep(3)
        
        # Generate mock network list
        networks = generate_mock_networks()
        
        return {"success": True, "networks": networks}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 開始捕獲握手包
@router.post("/capture/start")
async def start_capture(request: CaptureRequest, background_tasks: BackgroundTasks):
    try:
        # In a real environment, this would start a capture process
        # For example: airodump-ng -c <channel> --bssid <bssid> -w <output> <interface>
        
        if not request.output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"capture_{timestamp}"
        else:
            output_file = request.output_file
            
        # Simulate starting a capture process
        # background_tasks.add_task(run_capture_process, request.interface, request.bssid, request.channel, output_file)
        
        return {
            "success": True, 
            "message": "Handshake capture started",
            "capture_file": f"{output_file}.cap"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# 停止捕獲握手包
@router.post("/capture/stop")
async def stop_capture():
    try:
        # In a real environment, this would stop the capture process
        # For example: send a signal to the capture process or use pkill
        
        # Simulate stop delay
        await asyncio.sleep(1)
        
        return {"success": True, "message": "Handshake capture stopped"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 發送斷線訊號
@router.post("/deauth/send")
async def send_deauth(request: DeauthRequest):
    try:
        # In a real environment, this would send deauthentication signals
        # For example: aireplay-ng --deauth <packets> -a <bssid> <interface>
        
        # Simulate sending process
        logs = []
        for i in range(request.packets):
            # Simulate delay for each packet
            await asyncio.sleep(0.5)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            if request.broadcast:
                logs.append(f"[{timestamp}] Sending broadcast deauth packet ({i+1}/{request.packets}) to {request.bssid}")
            else:
                logs.append(f"[{timestamp}] Sending directed deauth packet ({i+1}/{request.packets}) to {request.bssid}")
        
        return {"success": True, "message": "Deauthentication signals completed", "logs": logs}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 驗證握手包
@router.post("/handshake/verify")
async def verify_handshake(request: dict):
    try:
        capture_file = request.get("capture_file")
        ssid = request.get("ssid")
        
        # In a real environment, this would verify the handshake validity
        # For example: aircrack-ng -w <wordlist> <capture_file>
        
        # Simulate verification process
        await asyncio.sleep(2)
        
        # Randomly decide if handshake is found (for simulation purposes)
        handshake_found = random.random() < 0.8
        
        if handshake_found:
            logs = [
                f"[+] Reading capture file: {capture_file}",
                "[+] Analyzing packet contents...",
                "[+] WPA handshake found (message pairs 1-4)",
                "[+] Handshake integrity verified",
                f"[+] SSID: {ssid}",
                "[+] Ready for password cracking"
            ]
            return {"success": True, "handshake_found": True, "logs": logs}
        else:
            logs = [
                f"[+] Reading capture file: {capture_file}",
                "[+] Analyzing packet contents...",
                "[-] No complete WPA handshake found",
                "[!] Suggestion: Go back and try sending more deauth signals"
            ]
            return {"success": True, "handshake_found": False, "logs": logs}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 啟動密碼破解
@router.post("/crack/start")
async def start_cracking(request: CrackRequest, background_tasks: BackgroundTasks):
    try:
        # In a real environment, this would start the cracking process
        # For example: aircrack-ng -w <wordlist> <capture_file>
        # Or using hashcat: hashcat -m 2500 -a 0 <file> <wordlist>
        
        # Store cracking task status
        task_id = str(uuid.uuid4())
        
        # Simulate cracking process
        # background_tasks.add_task(run_crack_process, task_id, request.capture_file, request.wordlist)
        
        return {
            "success": True, 
            "message": "Password cracking process started",
            "task_id": task_id
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# 獲取破解進度
@router.get("/crack/status/{task_id}")
async def get_crack_status(task_id: str):
    try:
        # In a real environment, this would check the status and progress of the cracking task
        
        # Simulate progress data
        # This is for demonstration only, actual implementation would need real status storage and retrieval
        seconds = random.randint(1, 100)
        speed = random.randint(4000, 8000)
        tested_keys = seconds * speed
        
        status = {
            "running": True,
            "seconds": seconds,
            "speed": speed,
            "tested_keys": tested_keys,
            "progress": min(100, seconds / 2),  # Simulate progress percentage
            "found": False
        }
        
        # Randomly simulate finding a password
        if random.random() < 0.01:  # 1% chance of finding password
            status["found"] = True
            status["password"] = generate_mock_password()
            status["running"] = False
        
        return {"success": True, "status": status}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 停止破解進程
@router.post("/crack/stop/{task_id}")
async def stop_cracking(task_id: str):
    try:
        # In a real environment, this would stop the cracking process
        
        return {"success": True, "message": "Password cracking process stopped"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 生成模擬密碼
def generate_mock_password():
    common_passwords = [
        "password123", "admin123", "welcome1", "123456789", "qwerty123", 
        "football", "iloveyou", "sunshine", "princess", "dragon123"
    ]
    return random.choice(common_passwords)

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