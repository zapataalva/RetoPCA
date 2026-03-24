from typing import Any, Dict

from src.domain.entities import ScanAnalysis
from src.domain.ports import AnalysisProvider, ScanRepository
from src.domain.exceptions import ScanNotFoundException


async def analyze_scan(
    repo: ScanRepository,
    provider: AnalysisProvider,
    scan_id: str,
) -> ScanAnalysis:
    scan = await repo.get_scan(scan_id)
    if not scan:
        raise ScanNotFoundException(scan_id)

    return await provider.analyze(scan)
