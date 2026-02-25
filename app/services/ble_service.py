from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BLEService(ABC):

    @abstractmethod
    def get_profiles(self) -> List[Dict]: ...

    @abstractmethod
    async def add_profile(self, profile: Dict) -> Dict[str, Any]: ...

    @abstractmethod
    async def delete_profile(self, name: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def start_beacon_emulator(self, profile_name: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def stop_beacon_emulator(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_beacon_emulator_status(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def start_airpods_emulator(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def stop_airpods_emulator(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_airpods_emulator_status(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_airpods_logs(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def scan_beacons(self, duration: int = 5) -> List[Dict[str, Any]]: ...
