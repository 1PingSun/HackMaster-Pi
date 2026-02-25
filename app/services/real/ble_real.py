import os
import subprocess
import signal
import psutil
import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException

from services.ble_service import BLEService
from api.mylib.beacon import beacon_emulator
from api.mylib.beacon.beacon_scanner import BeaconScanner

PROFILES_FILE = Path("data/beacon_profiles.json")
PROFILES_FILE.parent.mkdir(exist_ok=True)
if not PROFILES_FILE.exists():
    PROFILES_FILE.write_text("[]")

# Module-level global state
_running_process = None
_beacon_emulator_active = False


class BLERealService(BLEService):

    def get_profiles(self) -> List[Dict]:
        return json.loads(PROFILES_FILE.read_text())

    async def add_profile(self, profile: Dict) -> Dict[str, Any]:
        profiles = json.loads(PROFILES_FILE.read_text())
        profiles.append(profile)
        PROFILES_FILE.write_text(json.dumps(profiles, indent=2))
        return {"status": "success"}

    async def delete_profile(self, name: str) -> Dict[str, Any]:
        profiles = json.loads(PROFILES_FILE.read_text())
        profiles = [p for p in profiles if p["name"] != name]
        PROFILES_FILE.write_text(json.dumps(profiles, indent=2))
        return {"status": "success"}

    async def start_beacon_emulator(self, profile_name: str) -> Dict[str, Any]:
        global _beacon_emulator_active
        profiles = json.loads(PROFILES_FILE.read_text())
        profile = next((p for p in profiles if p["name"] == profile_name), None)
        if not profile:
            return {"success": False, "message": "Profile not found"}
        beacon_emulator.start_ibeacon(
            uuid=profile["uuid"],
            major=profile["major"],
            minor=profile["minor"],
            power=profile["power"]
        )
        _beacon_emulator_active = True
        return {"status": "started", "profile": profile["name"]}

    async def stop_beacon_emulator(self) -> Dict[str, Any]:
        global _beacon_emulator_active
        beacon_emulator.stop_ibeacon()
        _beacon_emulator_active = False
        return {"status": "stopped"}

    async def get_beacon_emulator_status(self) -> Dict[str, Any]:
        global _beacon_emulator_active
        if _beacon_emulator_active:
            return {"status": "running"}
        return {"status": "not_running"}

    async def start_airpods_emulator(self) -> Dict[str, Any]:
        global _running_process
        if _running_process and _running_process.poll() is None:
            return {"status": "already_running", "pid": _running_process.pid}
        try:
            env = os.environ.copy()
            cmd = ["sudo", "-E", "python3", "api/mylib/apple_bleee/adv_airpods.py"]
            with open("airpods_output.log", "w") as out_file, open("airpods_error.log", "w") as err_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=out_file,
                    stderr=err_file,
                    text=True,
                    env=env,
                    preexec_fn=os.setsid
                )
            _running_process = process
            return {"status": "started", "pid": process.pid}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")

    async def stop_airpods_emulator(self) -> Dict[str, Any]:
        global _running_process
        if not _running_process:
            return {"status": "not_running"}
        try:
            pid = _running_process.pid
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            gone, alive = psutil.wait_procs([parent], timeout=3)
            for p in alive:
                p.kill()
            _running_process = None
            return {"status": "stopped", "pid": pid}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")

    async def get_airpods_emulator_status(self) -> Dict[str, Any]:
        global _running_process
        if _running_process and _running_process.poll() is None:
            return {"status": "running", "pid": _running_process.pid}
        return {"status": "not_running"}

    async def get_airpods_logs(self) -> Dict[str, Any]:
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

    async def scan_beacons(self, duration: int = 5) -> List[Dict[str, Any]]:
        try:
            scanner = BeaconScanner(scan_duration=duration)
            beacons = await scanner.scan()
            return beacons
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to scan beacons: {str(e)}")
