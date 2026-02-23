from typing import Any, Dict

from services.rfid_service import RFIDService


class RFIDMockService(RFIDService):

    async def setup_pn532(self) -> Dict[str, Any]:
        return {"success": True, "message": "PN532 initialized (demo)"}

    async def identify_rfid(self) -> Dict[str, Any]:
        return {
            "success": True,
            "uid": "aabbccdd",
            "uid_length": 4,
            "type": ["Mifare Classic"],
            "atqa": "0004",
            "sak": "08"
        }

    async def write_uid(self, card_data: Dict, save_to_db: bool) -> Dict[str, Any]:
        return {"success": True, "message": "UID written successfully (demo)"}

    async def analyze_rfid(self, card_info: Dict) -> Dict[str, Any]:
        return {
            "success": True,
            "module": "RFID Defense",
            "issues": [
                {
                    "type": "STATIC_UID",
                    "severity": "MEDIUM",
                    "description": "Card uses a static UID which may be vulnerable to cloning"
                }
            ],
            "threat": {"score": 50, "status": "MEDIUM"}
        }
