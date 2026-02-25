from typing import Any, Dict, List

from fastapi import BackgroundTasks

from services.wifi_service import WiFiService


class WiFiMockService(WiFiService):

    async def get_interface_details(self) -> Dict[str, Any]:
        return {
            "success": True,
            "output": "wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
                      "        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255\n"
                      "wlan1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n",
            "message": "Network adapters listed successfully",
            "adapters": ["wlan0", "wlan1"]
        }

    async def get_interface_list(self) -> Dict[str, Any]:
        return {
            "success": True,
            "adapters": ["wlan0", "wlan1"],
            "count": 2
        }

    async def set_monitor_mode(self, interface: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": f"Monitor mode activated successfully for {interface} (demo)",
            "interface": interface
        }

    async def get_interface_status(self, interface: str) -> Dict[str, Any]:
        return {
            "success": True,
            "interface": interface,
            "mode": "Monitor",
            "status": "Monitor mode",
            "output": f"{interface}     IEEE 802.11  Mode:Monitor  Tx-Power=20 dBm\n"
        }

    async def scan_networks(self, interface: str, timeout: int) -> Dict[str, Any]:
        return {
            "success": True,
            "ap_list": [
                {
                    "bssid": "AA:BB:CC:DD:EE:01",
                    "ssid": "DemoNetwork_1",
                    "channel": 6,
                    "signal": -55,
                    "encryption": "WPA2"
                },
                {
                    "bssid": "AA:BB:CC:DD:EE:02",
                    "ssid": "DemoNetwork_2",
                    "channel": 11,
                    "signal": -70,
                    "encryption": "WPA2"
                },
                {
                    "bssid": "AA:BB:CC:DD:EE:03",
                    "ssid": "DemoNetwork_3",
                    "channel": 1,
                    "signal": -80,
                    "encryption": "WEP"
                }
            ],
            "interface": interface,
            "count": 3
        }

    async def set_channel(self, interface: str, channel: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": f"Channel {channel} set successfully for {interface} (demo)",
            "interface": interface,
            "channel": channel
        }

    async def start_capture(self, request: Any, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Traffic capture started (demo)",
            "capture_file": "demo_handshake-01.cap",
            "command": "sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:01 -w data/captures/demo_handshake wlan1"
        }

    async def stop_capture(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Traffic capture stopped (demo)"
        }

    async def send_deauth(self, interface: str, bssid: str, packets: int) -> Dict[str, Any]:
        return {
            "success": True,
            "message": f"Successfully sent {packets} deauth packets to {bssid} (demo)",
            "packets_sent": packets,
            "target_bssid": bssid,
            "interface": interface,
            "command": f"sudo aireplay-ng --deauth {packets} -a {bssid} {interface}",
            "output": ""
        }

    async def check_handshake(self, capture_file: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Found 1 handshake(s) in 1 network(s)",
            "capture_file": capture_file,
            "total_handshakes": 1,
            "total_networks": 1,
            "networks": [
                {
                    "number": 1,
                    "bssid": "AA:BB:CC:DD:EE:01",
                    "essid": "DemoNetwork_1",
                    "encryption": "WPA (1 handshake)",
                    "handshakes": 1
                }
            ],
            "command": f"sudo aircrack-ng data/captures/{capture_file}",
            "raw_output": ""
        }

    async def crack_password(self, capture_file: str, wordlist_file: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Password cracking completed (demo)",
            "capture_file": capture_file,
            "wordlist_file": wordlist_file,
            "password_found": "demo_password123",
            "command": f"sudo aircrack-ng data/captures/{capture_file} -w static/{wordlist_file}",
            "raw_output": "KEY FOUND! [ demo_password123 ]",
            "return_code": 0
        }

    async def generate_wordlist(self, output_filename: str, info_data: Dict[str, List[str]]) -> Dict[str, Any]:
        filename = output_filename if output_filename.endswith('.txt') else output_filename + '.txt'
        sample_lines = [
            "demo1234\n", "password1\n", "test123\n", "hello2024\n", "hackmaster\n",
            "demo5678\n", "password2\n", "test456\n", "hello2025\n", "hackmaster2\n"
        ]
        sample = ''.join(sample_lines)
        return {
            "success": True,
            "filename": filename,
            "count": 10,
            "sample": sample,
            "download_link": f"/static/wordlists/{filename}"
        }

    async def list_wordlists(self) -> Dict[str, Any]:
        return {
            "success": True,
            "wordlists": [
                {
                    "filename": "demo_wordlist.txt",
                    "path": "wordlists/demo_wordlist.txt",
                    "size": 1024,
                    "category": "custom",
                    "modified": "2025-01-01 00:00:00",
                    "download_link": "/static/wordlists/demo_wordlist.txt"
                },
                {
                    "filename": "rockyou_mini.txt",
                    "path": "wordlists/standard/rockyou_mini.txt",
                    "size": 204800,
                    "category": "standard",
                    "modified": "2025-01-01 00:00:00",
                    "download_link": "/static/wordlists/standard/rockyou_mini.txt"
                }
            ],
            "count": 2
        }

    async def delete_wordlist(self, filename: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message": f"Successfully deleted {filename} (demo)"
        }

    async def defense_scan(self, interface: str, timeout: int) -> Dict[str, Any]:
        return {
            "success": True,
            "module": "Wi-Fi Defense",
            "issues": [
                {
                    "type": "EVIL_TWIN",
                    "severity": "HIGH",
                    "description": "Potential Evil Twin AP detected: DemoNetwork_1",
                    "bssid": "AA:BB:CC:FF:EE:01",
                    "ssid": "DemoNetwork_1"
                }
            ],
            "threat": {"score": 75, "status": "HIGH"},
            "interface": interface
        }

    async def start_ap(self, config: Any) -> Dict[str, Any]:
        return {"success": True, "message": "AP started successfully"}

    async def stop_ap(self) -> Dict[str, Any]:
        return {"success": True, "message": "AP stopped successfully"}

    async def get_ap_status(self) -> Dict[str, Any]:
        return {
            "running": True,
            "ssid": "Mock_AP",
            "clients": 2,
            "uptime": "00:15:30"
        }

    async def start_ap_capture(self) -> Dict[str, Any]:
        return {"success": True, "message": "Capture started"}

    async def stop_ap_capture(self) -> Dict[str, Any]:
        return {"success": True, "message": "Capture stopped"}

    async def list_ap_captures(self) -> Dict[str, Any]:
        return {
            "success": True,
            "files": [
                {"name": "capture_01.pcap", "size": "1.2 MB", "date": "2023-10-25 10:30:00"},
                {"name": "capture_02.pcap", "size": "3.4 MB", "date": "2023-10-25 11:45:00"}
            ]
        }
