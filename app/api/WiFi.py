from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import asyncio
import random
from datetime import datetime

router = APIRouter(prefix="/WiFi", tags=["WiFi"])
templates = Jinja2Templates(directory="templates")

capture_active = False
ap_running = False
ap_capture_active = False
mock_capture_files = [
    {"id": "1", "filename": "ap_capture_demo.pcap", "size": 204800, "timestamp": "2025-01-01T12:00:00"}
]
mock_wordlists = [
    {"filename": "rockyou-top1000.txt", "path": "/usr/share/wordlists/rockyou-top1000.txt", "size": 8192, "category": "standard"},
    {"filename": "common-passwords.txt", "path": "/usr/share/wordlists/common-passwords.txt", "size": 4096, "category": "standard"},
]

class InterfaceRequest(BaseModel):
    interface: str

class ScanWifiRequest(BaseModel):
    interface: str
    timeout: int = 5

class ChannelRequest(BaseModel):
    interface: str
    channel: int

class CaptureRequest(BaseModel):
    interface: str
    bssid: str
    channel: int

class DeauthRequest(BaseModel):
    interface: str
    bssid: str
    packets: int = 10

class HandshakeCheckRequest(BaseModel):
    capture_file: str = ""

class APStartRequest(BaseModel):
    ssid: str
    security: str = "wpa2"
    password: str = ""
    channel: str = "6"
    hidden: bool = False
    captive_portal: bool = False
    internet_sharing: bool = False
    mac_address: str = ""

class WordlistGenerateRequest(BaseModel):
    output_filename: str
    info_data: dict

class DefenseScanRequest(BaseModel):
    interface: str
    timeout: int = 10

class CrackRequest(BaseModel):
    wordlist_file: str = ""

@router.get("/ap-emulator", response_class=HTMLResponse)
def read_ap_emulator(request: Request):
    return templates.TemplateResponse(request=request, name="WiFi/ap-emulator.html", context={"message": "AP Emulator"})

@router.get("/wifi-cracker", response_class=HTMLResponse)
def read_wifi_cracker(request: Request):
    return templates.TemplateResponse(request=request, name="WiFi/wifi-cracker.html", context={"message": "WiFi Cracker"})

@router.get("/wifi-scanner", response_class=HTMLResponse)
def read_wifi_scanner(request: Request):
    return templates.TemplateResponse(request=request, name="WiFi/wifi-scanner.html", context={"message": "WiFi Scanner"})

@router.get("/wordlist-generator", response_class=HTMLResponse)
def read_wordlist_generator(request: Request):
    return templates.TemplateResponse(request=request, name="WiFi/wordlist-generator.html", context={"message": "Wordlist Generator"})

@router.post("/interface/up")
async def interface_up(request: InterfaceRequest):
    return {"success": True, "message": f"Demo: Interface {request.interface} brought up"}

@router.post("/interface/monitor")
async def interface_monitor(request: InterfaceRequest):
    return {"success": True, "message": f"Demo: Monitor mode activated on {request.interface}", "interface": request.interface}

@router.get("/interface/status")
async def get_interface_status(interface: str):
    return {
        "success": True,
        "interface": interface,
        "mode": "Monitor",
        "status": "Monitor mode (Demo)",
        "output": "Mock iwconfig output..."
    }

@router.post("/ap/scan")
async def scan_wifi(request: ScanWifiRequest):
    await asyncio.sleep(request.timeout)
    mock_aps = [
        {"ssid": "Demo_WiFi_1", "bssid": "00:11:22:33:44:55", "channel": 1, "signal": -45, "encryption": "WPA2"},
        {"ssid": "Demo_WiFi_2", "bssid": "AA:BB:CC:DD:EE:FF", "channel": 6, "signal": -60, "encryption": "WPA3"},
        {"ssid": "Guest_Network", "bssid": "12:34:56:78:90:AB", "channel": 11, "signal": -80, "encryption": "OPEN"}
    ]
    return {
        "success": True,
        "ap_list": mock_aps,
        "interface": request.interface,
        "count": len(mock_aps)
    }

@router.post("/interface/channel")
async def set_interface_channel(request: ChannelRequest):
    return {"success": True, "message": f"Demo: Channel {request.channel} set on {request.interface}", "interface": request.interface, "channel": request.channel}

@router.post("/capture/start")
async def start_capture(request: CaptureRequest, background_tasks: BackgroundTasks):
    global capture_active
    capture_active = True
    return {"success": True, "message": "Demo: Traffic capture started", "capture_file": "deauth_handshake-01.cap", "command": "sudo airodump-ng mock"}

@router.post("/capture/stop")
async def stop_capture():
    global capture_active
    capture_active = False
    return {"success": True, "message": "Demo: Traffic capture stopped"}

@router.post("/deauth/send")
async def send_deauth(request: DeauthRequest):
    await asyncio.sleep(1)
    return {"success": True, "message": f"Demo: Successfully sent {request.packets} deauth packets to {request.bssid}", "packets_sent": request.packets}

@router.post("/handshake/check")
async def check_handshake(request: HandshakeCheckRequest):
    return {
        "success": True,
        "message": "Demo: Found 1 handshake(s) in 1 network(s)",
        "capture_file": request.capture_file or "deauth_handshake-01.cap",
        "total_handshakes": 1,
        "total_networks": 1,
        "networks": [{"number": 1, "bssid": "00:11:22:33:44:55", "essid": "Demo_WiFi_1", "encryption": "WPA2 (1 handshake)", "handshakes": 1}],
        "command": "aircrack-ng mock",
        "raw_output": "Mock aircrack-ng output detailing 1 handshake..."
    }

# --- Interface ---

@router.get("/interface/details")
async def get_interface_details():
    return {
        "success": True,
        "message": "Demo: Found 2 network adapter(s)",
        "adapters": ["wlan0", "wlan1"],
        "output": "wlan0: IEEE 802.11 Mode:Managed\nwlan1: IEEE 802.11 Mode:Monitor"
    }

@router.get("/interface/list")
async def get_interface_list():
    return {"success": True, "adapters": ["wlan0", "wlan1"]}

@router.post("/interface/monitorMode")
async def interface_monitor_mode(request: InterfaceRequest):
    return {"success": True, "message": f"Demo: Monitor mode activated on {request.interface}", "interface": request.interface}

# --- AP Emulator ---

@router.post("/ap/start")
async def start_ap(request: APStartRequest):
    global ap_running
    ap_running = True
    return {"success": True, "message": f"Demo: Access point '{request.ssid}' started on channel {request.channel}"}

@router.post("/ap/stop")
async def stop_ap():
    global ap_running, ap_capture_active
    ap_running = False
    ap_capture_active = False
    return {"success": True, "message": "Demo: Access point stopped"}

@router.get("/ap/status")
async def get_ap_status():
    clients = []
    if ap_running:
        clients = [
            {"mac": "AA:BB:CC:DD:EE:01", "ip": "192.168.4.2", "hostname": "demo-device-1", "connected_since": "00:01:23"},
            {"mac": "AA:BB:CC:DD:EE:02", "ip": "192.168.4.3", "hostname": "demo-device-2", "connected_since": "00:00:45"},
        ]
    return {"success": True, "connected_clients": clients}

@router.post("/ap/capture/start")
async def start_ap_capture():
    global ap_capture_active
    ap_capture_active = True
    return {"success": True, "message": "Demo: Packet capture started"}

@router.post("/ap/capture/stop")
async def stop_ap_capture():
    global ap_capture_active
    ap_capture_active = False
    new_file = {
        "id": str(len(mock_capture_files) + 1),
        "filename": f"ap_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap",
        "size": random.randint(50000, 500000),
        "timestamp": datetime.now().isoformat()
    }
    mock_capture_files.append(new_file)
    return {"success": True, "message": "Demo: Packet capture stopped", "capture_file": new_file["filename"]}

@router.get("/ap/capture/list")
async def list_ap_captures():
    return {"success": True, "captures": mock_capture_files}

@router.get("/ap/capture/download/{capture_id}")
async def download_ap_capture(capture_id: str):
    return {"success": True, "message": f"Demo: Download not available in demo mode for capture {capture_id}"}

# --- Wordlists ---

@router.get("/wordlists/list")
async def list_wordlists():
    return {"success": True, "wordlists": mock_wordlists}

@router.post("/wordlist-generator")
async def generate_wordlist(request: WordlistGenerateRequest):
    await asyncio.sleep(1)
    filename = request.output_filename if request.output_filename.endswith(".txt") else request.output_filename + ".txt"
    sample_passwords = ["password123", "admin2024", "hackmaster1", "qwerty123", "letmein"]
    new_wordlist = {
        "filename": filename,
        "path": f"/tmp/{filename}",
        "size": random.randint(2048, 20480),
        "category": "custom"
    }
    mock_wordlists.append(new_wordlist)
    return {
        "success": True,
        "filename": filename,
        "count": random.randint(100, 5000),
        "sample": "\n".join(sample_passwords),
        "download_link": f"/WiFi/wordlists/custom/{filename}"
    }

@router.delete("/wordlists/custom/{filename}")
async def delete_wordlist(filename: str):
    global mock_wordlists
    before = len(mock_wordlists)
    mock_wordlists = [w for w in mock_wordlists if w["filename"] != filename]
    if len(mock_wordlists) < before:
        return {"success": True, "message": f"Deleted {filename}"}
    return {"success": False, "message": f"{filename} not found"}

# --- Crack ---

@router.post("/capture/crack")
async def crack_capture(request: CrackRequest):
    await asyncio.sleep(2)
    return {
        "success": True,
        "message": "Demo: Password found!",
        "password_found": True,
        "password": "demo_password123",
        "wordlist": request.wordlist_file or "rockyou-top1000.txt"
    }

# --- Defense ---

@router.post("/defense/scan")
async def defense_scan(request: DefenseScanRequest):
    await asyncio.sleep(request.timeout * 0.2)
    return {
        "success": True,
        "threat": {"score": 65, "status": "WARNING"},
        "issues": [
            {"type": "open_network", "risk": "HIGH", "detail": "Demo: Open network detected (no encryption)"},
            {"type": "weak_password", "risk": "MEDIUM", "detail": "Demo: Weak WPA2 password on Demo_WiFi_1"},
            {"type": "wps_enabled", "risk": "LOW", "detail": "Demo: WPS enabled on Guest_Network"},
        ]
    }
