from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.domain.entities import ScanAnalysis, ScanResult

class ScanRepository(ABC):
    @abstractmethod
    async def create_scan(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def update_scan(self, scan_id: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class PluginRunner(ABC):
    @abstractmethod
    async def run(self, swagger_path: str, overrides: Optional[Dict[str, Any]] = None) -> ScanResult:
        raise NotImplementedError


class AnalysisProvider(ABC):
    @abstractmethod
    async def analyze(self, scan: Dict[str, Any]) -> ScanAnalysis:
        raise NotImplementedError
