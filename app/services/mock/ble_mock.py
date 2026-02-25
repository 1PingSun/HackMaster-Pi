from typing import Any, Dict, List

from services.ble_service import BLEService


class BLEMockService(BLEService):

    def get_profiles(self) -> List[Dict]:
        return [
            {
                "name": "Demo iBeacon 1",
                "uuid": "12345678-1234-1234-1234-123456789abc",
                "major": 1,
                "minor": 1,
                "power": -59
            },
            {
                "name": "Demo iBeacon 2",
                "uuid": "87654321-4321-4321-4321-cba987654321",
                "major": 2,
                "minor": 2,
                "power": -65
            }
        ]

    async def add_profile(self, profile: Dict) -> Dict[str, Any]:
        return {"status": "success"}

    async def delete_profile(self, name: str) -> Dict[str, Any]:
        return {"status": "success"}

    async def start_beacon_emulator(self, profile_name: str) -> Dict[str, Any]:
        return {"status": "started", "profile": profile_name}

    async def stop_beacon_emulator(self) -> Dict[str, Any]:
        return {"status": "stopped"}

    async def get_beacon_emulator_status(self) -> Dict[str, Any]:
        return {"status": "running"}

    async def start_airpods_emulator(self) -> Dict[str, Any]:
        return {"status": "started", "pid": 99999}

    async def stop_airpods_emulator(self) -> Dict[str, Any]:
        return {"status": "stopped", "pid": 99999}

    async def get_airpods_emulator_status(self) -> Dict[str, Any]:
        return {"status": "running", "pid": 99999}

    async def get_airpods_logs(self) -> Dict[str, Any]:
        return {
            "output": "[demo] AirPods emulator running...\n[demo] Broadcasting BLE advertisement\n",
            "errors": ""
        }

    async def scan_beacons(self, duration: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Demo iBeacon 1",
                "rssi": -59,
                "uuid": "12345678-1234-1234-1234-123456789abc",
                "major": 1,
                "minor": 1,
                "tx_power": -59,
                "type": "iBeacon"
            },
            {
                "mac": "11:22:33:44:55:66",
                "name": "Demo iBeacon 2",
                "rssi": -65,
                "uuid": "87654321-4321-4321-4321-cba987654321",
                "major": 2,
                "minor": 2,
                "tx_power": -65,
                "type": "iBeacon"
            }
        ]
