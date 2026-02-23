from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IRService(ABC):

    @abstractmethod
    async def start_recording(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def cancel_recording(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def transmit(self, signal_data: str, format: Optional[str]) -> Dict[str, Any]: ...

    @abstractmethod
    async def enumerate_code(self, device_type: str, brand: str, protocol: str, function: str, code_index: int) -> Dict[str, Any]: ...
