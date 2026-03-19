from pydantic import BaseModel
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv("app.env")

class Settings(BaseModel):
    request_timeout_seconds: float = 15.0
    connect_timeout_seconds: float = 7.0
    total_scan_timeout_seconds: float = 40.0
    user_agent: str = "SecurityScan"

    mongo_uri: str
    mongo_db_name: str
    mongo_collection_name: str

@lru_cache()
def get_settings() -> Settings:
    return Settings(
        mongo_uri=os.getenv("MONGO_URI"),
        mongo_db_name=os.getenv("MONGO_DB"),
        mongo_collection_name=os.getenv("MONGO_COLLECTION"),
    )
