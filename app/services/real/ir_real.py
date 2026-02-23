import asyncio
import time
import random
from typing import Any, Dict, Optional

from services.ir_service import IRService

# Module-level global state
_ir_recording = False
_ir_signal = None
_ir_record_start_time = None


def generate_ir_code(device_type, brand, protocol, function, index):
    base_value = index * 37 + (ord(function[0]) if function else 0)
    return format(base_value % 65536, '04X') + format((base_value * 17) % 65536, '04X')


async def _simulate_ir_reception():
    global _ir_recording, _ir_signal
    await asyncio.sleep(3)
    if _ir_recording:
        _ir_signal = {
            "data": "010101010110101010100101010101011010101010010101010101101010",
            "format": "NEC",
            "length": 32
        }
        _ir_recording = False


class IRRealService(IRService):

    async def start_recording(self) -> Dict[str, Any]:
        global _ir_recording, _ir_signal, _ir_record_start_time
        try:
            if _ir_recording:
                return {"success": False, "message": "Already recording"}
            _ir_recording = True
            _ir_signal = None
            _ir_record_start_time = time.time()
            asyncio.create_task(_simulate_ir_reception())
            return {"success": True, "message": "IR recording started"}
        except Exception as e:
            _ir_recording = False
            return {"success": False, "message": str(e)}

    async def cancel_recording(self) -> Dict[str, Any]:
        global _ir_recording, _ir_signal
        try:
            _ir_recording = False
            _ir_signal = None
            return {"success": True, "message": "Recording cancelled"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_status(self) -> Dict[str, Any]:
        global _ir_recording, _ir_signal, _ir_record_start_time
        if _ir_recording and _ir_record_start_time:
            if time.time() - _ir_record_start_time > 15:
                _ir_recording = False
                return {"status": "timeout", "message": "Recording timed out"}
        if _ir_recording:
            return {"status": "recording"}
        elif _ir_signal:
            return {"status": "completed", "signal": _ir_signal}
        else:
            return {"status": "idle"}

    async def transmit(self, signal_data: str, format: Optional[str]) -> Dict[str, Any]:
        try:
            await asyncio.sleep(1)
            return {"success": True, "message": "Signal transmitted successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def enumerate_code(self, device_type: str, brand: str, protocol: str, function: str, code_index: int) -> Dict[str, Any]:
        try:
            await asyncio.sleep(0.1)
            code_hex = generate_ir_code(device_type, brand, protocol, function, code_index)
            response_detected = random.random() < 0.05
            return {
                "success": True,
                "code_index": code_index,
                "code_hex": code_hex,
                "protocol": protocol if protocol != "all" else random.choice(["NEC", "SONY", "RC5", "RC6", "SAMSUNG"]),
                "response": response_detected,
                "bits": 32
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
