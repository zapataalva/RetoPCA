from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

@dataclass
class PayloadResult:
    payload: str
    payload_type: str
    location: str 
    status_code: Optional[int]
    response_time_ms: Optional[float]
    response_size: Optional[int]
    evidence: Optional[str] = None
    error: Optional[str] = None
    indicators: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EndpointResult:
    method: str
    path: str
    full_url: str
    params: Dict[str, Any]
    body: Optional[Dict[str, Any]]
    results: List[PayloadResult] = field(default_factory=list)

@dataclass
class Metrics:
    total_endpoints: int
    total_requests: int
    total_failures: int
    avg_response_ms: float
    by_status_code: Dict[str, int]
    by_payload_type: Dict[str, int]
    indicators_summary: Dict[str, int]

@dataclass
class ScanResult:
    scan_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    swagger_title: Optional[str]
    swagger_version: Optional[str]
    base_url: Optional[str]
    endpoints: List[EndpointResult] = field(default_factory=list)
    metrics: Optional[Metrics] = None

@dataclass
class ScanJob:
    scan_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    swagger_title: Optional[str]
    swagger_version: Optional[str]
    base_url: Optional[str]
    result: Optional[ScanResult] = None


class CreateScanResponse(BaseModel):
    scan_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ScanResponseModel(BaseModel):
    scan_id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    swagger_title: Optional[str] = None
    swagger_version: Optional[str] = None
    base_url: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
