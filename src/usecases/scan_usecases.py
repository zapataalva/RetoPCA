from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from src.domain.ports import PluginRunner, ScanRepository

async def start_scan_sync(
    repo: ScanRepository,
    runner: PluginRunner,
    swagger_path: str,
    swagger_info: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any] | None, str, str | None]:
    now = datetime.now(timezone.utc)
    scan_id = str(uuid4())

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
        return scan_id, None, "failed", error_msg

    try:
        await repo.update_scan(scan_id, {"status": "running", "updated_at": datetime.now(timezone.utc)})
    except Exception as exc:
        error_msg = f"update_scan(running): {type(exc).__name__}: {str(exc) or repr(exc)}"
        return scan_id, None, "failed", error_msg
    try:
        result = await runner.run(swagger_path, overrides)
        await repo.update_scan(
            scan_id,
            {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc),
                "result": result,
            },
        )
        return scan_id, result, "completed", None
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
        return scan_id, None, "failed", error_msg


async def get_scan(repo: ScanRepository, scan_id: str) -> Dict[str, Any] | None:
    return await repo.get_scan(scan_id)
