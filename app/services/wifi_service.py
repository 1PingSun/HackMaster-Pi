from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks


class WiFiService(ABC):

    @abstractmethod
    async def get_interface_details(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_interface_list(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def set_monitor_mode(self, interface: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_interface_status(self, interface: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def scan_networks(self, interface: str, timeout: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def set_channel(self, interface: str, channel: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def start_capture(self, request: Any, background_tasks: BackgroundTasks) -> Dict[str, Any]: ...

    @abstractmethod
    async def stop_capture(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def send_deauth(self, interface: str, bssid: str, packets: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def check_handshake(self, capture_file: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def crack_password(self, capture_file: str, wordlist_file: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def generate_wordlist(self, output_filename: str, info_data: Dict[str, List[str]]) -> Dict[str, Any]: ...

    @abstractmethod
    async def list_wordlists(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def delete_wordlist(self, filename: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def defense_scan(self, interface: str, timeout: int) -> Dict[str, Any]: ...
