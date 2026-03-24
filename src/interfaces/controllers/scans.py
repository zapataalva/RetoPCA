import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.domain.ports import AnalysisProvider, PluginRunner, ScanRepository
from src.core.dependencies import get_scan_repository
from src.usecases.analysis_usecases import analyze_scan
from src.usecases.scan_usecases import get_scan, start_scan_sync
from dataclasses import asdict

from src.domain.entities import AnalysisResponseModel, CreateScanResponse, ScanResponseModel
from src.domain.exceptions import (
    InvalidFileTypeException,
    InvalidJsonException,
    InvalidOverridesException,
    ScanNotFoundException,
)
from src.infrastructure.services.analysis_provider import LocalAnalysisProvider
from src.infrastructure.plugins.dast_scanner import DastScannerRunner

router = APIRouter()


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    if base_url.startswith("http://") or base_url.startswith("https://"):
        return base_url
    return f"https://{base_url.lstrip('/')}"


def _extract_swagger_info(spec: Dict[str, Any]) -> Dict[str, Any]:
    info = spec.get("info") or {}
    base_url = None
    host = spec.get("host")
    base_path = spec.get("basePath") or ""
    schemes = spec.get("schemes") or []
    if host:
        scheme = schemes[0] if schemes else "https"
        base_url = _normalize_base_url(f"{scheme}://{host}{base_path}")
    else:
        servers = spec.get("servers") or []
        base_url = _normalize_base_url(servers[0].get("url") if servers else None)
    return {"title": info.get("title"), "version": info.get("version"), "base_url": base_url}


@router.post("/scans", response_model=CreateScanResponse)
async def create_scan(
    file: UploadFile = File(...),
    overrides: str | None = Form(None),
    repo: ScanRepository = Depends(get_scan_repository),
) -> CreateScanResponse:
    runner: PluginRunner = DastScannerRunner()
    if not file.filename.lower().endswith(".json"):
        raise InvalidFileTypeException(file.filename)

    content = await file.read()
    try:
        spec = json.loads(content.decode("utf-8"))
    except Exception as exc:
        raise InvalidJsonException() from exc

    info = _extract_swagger_info(spec)
    overrides_dict = None
    if overrides:
        try:
            overrides_dict = json.loads(overrides)
        except Exception as exc:
            raise InvalidOverridesException() from exc

    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=tmp_dir) as f:
        f.write(content)
        swagger_path = f.name
    
    print('Este es el swagger desde el controller', info)

    scan_id, result, status, error = await start_scan_sync(repo, runner, swagger_path, info, overrides_dict)
    return CreateScanResponse(scan_id=scan_id, status=status, result=result, error=error)


@router.get("/scans/{scan_id}", response_model=ScanResponseModel)
async def read_scan(scan_id: str, repo: ScanRepository = Depends(get_scan_repository)) -> ScanResponseModel:
    doc = await get_scan(repo, scan_id)
    if not doc:
        raise ScanNotFoundException(scan_id)

    return ScanResponseModel(   
        scan_id=doc.get("_id"),
        status=doc.get("status"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
        swagger_title=doc.get("swagger_title"),
        swagger_version=doc.get("swagger_version"),
        base_url=doc.get("base_url"),
        result=doc.get("result"),
        error=doc.get("error"),
    )


@router.post("/scans/{scan_id}/analysis", response_model=AnalysisResponseModel)
async def analyze_scan_endpoint(
    scan_id: str, repo: ScanRepository = Depends(get_scan_repository)
) -> AnalysisResponseModel:
    provider: AnalysisProvider = LocalAnalysisProvider()
    analysis = await analyze_scan(repo, provider, scan_id)
    return AnalysisResponseModel(scan_id=scan_id, analysis=asdict(analysis), error=None)

