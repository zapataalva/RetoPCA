from src.core.config import get_settings
from src.infrastructure.repositories.mongo_scan_repository import MongoScanRepository

def get_scan_repository():
    settings = get_settings()
    return MongoScanRepository(settings)
