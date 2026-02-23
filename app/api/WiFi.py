from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict

from services.wifi_service import WiFiService
from services.real.wifi_real import WiFiRealService

router = APIRouter(
    prefix="/WiFi",
    tags=["WiFi"]
)

templates = Jinja2Templates(directory="templates")


# ---------- Pydantic models ----------

class APConfig(BaseModel):
    ssid: str
    security: str
    password: Optional[str] = ""
    channel: str
    hidden: bool = False
    captive_portal: bool = False
    internet_sharing: bool = False
    mac_address: Optional[str] = None

class CaptureFile(BaseModel):
    id: str
    filename: str
    path: str
    size: int
    timestamp: str

class ScanRequest(BaseModel):
    bands: Dict[str, bool]
    show_hidden: bool = False

class NetworkInterfaceRequest(BaseModel):
    interface: str

class ScanWifiRequest(BaseModel):
    interface: str
    timeout: int = 10

class CaptureRequest(BaseModel):
    interface: str
    bssid: str
    channel: int
    output_file: Optional[str] = None

class DeauthRequest(BaseModel):
    interface: str
    bssid: str
    packets: int = 10
    broadcast: bool = True

class CrackRequest(BaseModel):
    capture_file: str
    wordlist: str
    hash_mode: Optional[str] = "2500"
    attack_mode: Optional[str] = "0"
    ssid: Optional[str] = None

class WordlistRequest(BaseModel):
    output_filename: str
    info_data: Dict[str, List[str]]

class ChannelRequest(BaseModel):
    interface: str
    channel: str

class HandshakeCheckRequest(BaseModel):
    capture_file: Optional[str] = "deauth_handshake-01.cap"

class CrackPasswordRequest(BaseModel):
    capture_file: Optional[str] = "deauth_handshake-01.cap"
    wordlist_file: str


# ---------- Dependency ----------

def get_wifi_service() -> WiFiService:
    return WiFiRealService()


# ---------- HTML page routes ----------

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


# ---------- API routes ----------

@router.get("/interface/details")
async def list_adapters(service: WiFiService = Depends(get_wifi_service)):
    return await service.get_interface_details()

@router.get("/interface/list")
async def get_adapter_names(service: WiFiService = Depends(get_wifi_service)):
    return await service.get_interface_list()

@router.post("/interface/monitorMode")
async def activate_monitor_mode(request: NetworkInterfaceRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.set_monitor_mode(request.interface)

@router.get("/interface/status")
async def get_interface_status(interface: str, service: WiFiService = Depends(get_wifi_service)):
    return await service.get_interface_status(interface)

@router.post("/ap/scan")
async def scan_wifi(request: ScanWifiRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.scan_networks(request.interface, request.timeout)

@router.post("/interface/channel")
async def set_interface_channel(request: ChannelRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.set_channel(request.interface, request.channel)

@router.post("/capture/start")
async def start_capture(request: CaptureRequest, background_tasks: BackgroundTasks, service: WiFiService = Depends(get_wifi_service)):
    return await service.start_capture(request, background_tasks)

@router.post("/capture/stop")
async def stop_capture(service: WiFiService = Depends(get_wifi_service)):
    return await service.stop_capture()

@router.post("/deauth/send")
async def send_deauth(request: DeauthRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.send_deauth(request.interface, request.bssid, request.packets)

@router.post("/handshake/check")
async def check_handshake(request: HandshakeCheckRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.check_handshake(request.capture_file)

@router.post("/capture/crack")
async def crack_password(request: CrackPasswordRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.crack_password(request.capture_file, request.wordlist_file)

@router.post("/wordlist-generator")
async def generate_wordlist(request: WordlistRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.generate_wordlist(request.output_filename, request.info_data)

@router.get("/wordlists/list")
async def list_wordlists(service: WiFiService = Depends(get_wifi_service)):
    return await service.list_wordlists()

@router.delete("/wordlists/custom/{filename}")
async def delete_custom_wordlist(filename: str, service: WiFiService = Depends(get_wifi_service)):
    return await service.delete_wordlist(filename)

@router.post("/defense/scan")
async def defense_scan(request: ScanWifiRequest, service: WiFiService = Depends(get_wifi_service)):
    return await service.defense_scan(request.interface, request.timeout)
