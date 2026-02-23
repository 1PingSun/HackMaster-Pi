from typing import Any, Dict, Optional

from services.ir_service import IRService

# Module-level state for singleton mock
_mock_recording = False
_mock_signal_ready = False


class IRMockService(IRService):

    async def start_recording(self) -> Dict[str, Any]:
        global _mock_recording, _mock_signal_ready
        _mock_recording = True
        _mock_signal_ready = False
        return {"success": True, "message": "IR recording started (demo)"}

    async def cancel_recording(self) -> Dict[str, Any]:
        global _mock_recording, _mock_signal_ready
        _mock_recording = False
        _mock_signal_ready = False
        return {"success": True, "message": "Recording cancelled (demo)"}

    async def get_status(self) -> Dict[str, Any]:
        global _mock_recording, _mock_signal_ready
        if _mock_recording:
            # Simulate signal received after first status poll
            _mock_recording = False
            _mock_signal_ready = True
        if _mock_signal_ready:
            return {
                "status": "completed",
                "signal": {
                    "data": "010101010110101010100101010101011010101010010101010101101010",
                    "format": "NEC",
                    "length": 32
                }
            }
        return {"status": "idle"}

    async def transmit(self, signal_data: str, format: Optional[str]) -> Dict[str, Any]:
        return {"success": True, "message": "Signal transmitted successfully (demo)"}

    async def enumerate_code(self, device_type: str, brand: str, protocol: str, function: str, code_index: int) -> Dict[str, Any]:
        base_value = code_index * 37 + ord(function[0]) if function else code_index * 37
        code_hex = format(base_value % 65536, '04X') + format((base_value * 17) % 65536, '04X')
        return {
            "success": True,
            "code_index": code_index,
            "code_hex": code_hex,
            "protocol": protocol if protocol != "all" else "NEC",
            "response": False,
            "bits": 32
        }
