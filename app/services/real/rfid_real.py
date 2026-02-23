import asyncio
import binascii
from typing import Any, Dict

from fastapi.responses import JSONResponse

from services.rfid_service import RFIDService
from api.mylib.RFIDlib import main as RFIDlib
from api.mylib.defense.defense_manager import DefenseManager


class RFIDRealService(RFIDService):

    async def setup_pn532(self) -> Dict[str, Any]:
        try:
            result = RFIDlib.setup()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def identify_rfid(self) -> Dict[str, Any]:
        try:
            found = RFIDlib.iso14443a_identify()
            while not found["success"]:
                await asyncio.sleep(0.1)
                found = RFIDlib.iso14443a_identify()
            return found
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_uid(self, card_data: Dict, save_to_db: bool) -> Dict[str, Any]:
        try:
            new_uid_hex = card_data.get("uid")
            if not new_uid_hex:
                return {"success": False, "error": "UID is required"}
            if len(new_uid_hex) != 8:
                return {"success": False, "error": "UID must be 8 hexadecimal characters"}
            try:
                binascii.unhexlify(new_uid_hex)
            except Exception:
                return {"success": False, "error": "UID contains invalid characters"}
            result = RFIDlib.write_uid(new_uid_hex)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_rfid(self, card_info: Dict) -> Dict[str, Any]:
        try:
            defense_manager = DefenseManager()
            result = defense_manager.run_rfid_defense(card_info)
            return {
                "success": True,
                "module": result["module"],
                "issues": result["issues"],
                "threat": result["threat"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "threat": {"score": 0, "status": "UNKNOWN"}
            }
