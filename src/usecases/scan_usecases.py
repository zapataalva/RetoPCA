from datetime import datetime, timezone
from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from src.domain.ports import PluginRunner, ScanRepository
from src.domain.exceptions import (
    ScanPersistenceException,
    ScannerExecutionException,
    SwaggerBaseUrlMissingException,
)

async def start_scan_sync(
    repo: ScanRepository,
    runner: PluginRunner,
    swagger_path: str,
    swagger_info: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any] | None, str, str | None]:
    now = datetime.now(timezone.utc)
    scan_id = str(uuid4())

    base_url = swagger_info.get("base_url")
    if not base_url:
        raise SwaggerBaseUrlMissingException()

    try:
        print('ESTE ES EL BASE_URL',swagger_info.get("base_url"))
        await repo.create_scan(
            {
                "_id": scan_id,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "swagger_title": swagger_info.get("title"),
                "swagger_version": swagger_info.get("version"),
                "base_url": swagger_info.get("base_url"),
                "result": None,
            }
        )
    except Exception as exc:
        error_msg = f"create_scan: {type(exc).__name__}: {str(exc) or repr(exc)}"
        raise ScanPersistenceException(error_msg) from exc

    try:
        await repo.update_scan(scan_id, {"status": "running", "updated_at": datetime.now(timezone.utc)})
    except Exception as exc:
        error_msg = f"update_scan(running): {type(exc).__name__}: {str(exc) or repr(exc)}"
        raise ScanPersistenceException(error_msg) from exc
    try:
        result = await runner.run(swagger_path, overrides)
        result_dict = asdict(result)
        result_dict.pop("scan_id", None)
        result_dict.pop("created_at", None)
        result_dict.pop("updated_at", None)
        await repo.update_scan(
            scan_id,
            {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc),
                "result": result_dict,
            },
        )
        return scan_id, result_dict, "completed", None
    except Exception as exc:
        error_msg = f"runner.run: {type(exc).__name__}: {str(exc) or repr(exc)}"
        try:
            await repo.update_scan(
                scan_id,
                {
                    "status": "failed",
                    "updated_at": datetime.now(timezone.utc),
                    "error": error_msg,
                },
            )
        except Exception:
            pass
        raise ScannerExecutionException(error_msg) from exc


async def get_scan(repo: ScanRepository, scan_id: str) -> Dict[str, Any] | None:
    return await repo.get_scan(scan_id)

