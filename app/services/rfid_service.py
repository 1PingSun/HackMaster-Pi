from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RFIDService(ABC):

    @abstractmethod
    async def setup_pn532(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def identify_rfid(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def write_uid(self, card_data: Dict, save_to_db: bool) -> Dict[str, Any]: ...

    @abstractmethod
    async def analyze_rfid(self, card_info: Dict) -> Dict[str, Any]: ...
