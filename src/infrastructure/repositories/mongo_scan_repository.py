from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config import Settings
from src.domain.ports import ScanRepository


class MongoScanRepository(ScanRepository):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncIOMotorClient(settings.mongo_uri)
        db = self._client[settings.mongo_db_name]
        self._col = db[settings.mongo_collection_name]

    async def create_scan(self, data: Dict[str, Any]) -> str:
        await self._col.insert_one(data)
        return str(data.get("_id"))

    async def update_scan(self, scan_id: str, data: Dict[str, Any]) -> None:
        await self._col.update_one({"_id": scan_id}, {"$set": data})

    async def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        return await self._col.find_one({"_id": scan_id})
