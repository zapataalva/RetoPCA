from typing import Any, Dict, Optional

from src.domain.entities import ScanAnalysis
from src.domain.ports import AnalysisProvider, ScanRepository


async def analyze_scan(
    repo: ScanRepository,
    provider: AnalysisProvider,
    scan_id: str,
) -> Optional[ScanAnalysis]:
    scan = await repo.get_scan(scan_id)
    if not scan:
        return None

    return await provider.analyze(scan)
