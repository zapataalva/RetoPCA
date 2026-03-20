from __future__ import annotations

from typing import Any, Dict, List

from src.domain.entities import AnalysisFinding, AnalysisIndicators, AnalysisSummary, ScanAnalysis
from src.domain.ports import AnalysisProvider


class LocalAnalysisProvider(AnalysisProvider):
    async def analyze(self, scan: Dict[str, Any]) -> ScanAnalysis:
        result = scan.get("result") or {}
        metrics = result.get("metrics") or {}
        indicators = metrics.get("indicators_summary") or {}
        by_status = metrics.get("by_status_code") or {}

        sqli_hits = int(indicators.get("sqli_error_hint") or 0)
        xss_hits = int(indicators.get("xss_reflected") or 0)
        failures = int(metrics.get("total_failures") or 0)
        total_requests = int(metrics.get("total_requests") or 0)
        avg_response_ms = metrics.get("avg_response_ms")

        risk_level = _risk_level(sqli_hits, xss_hits, failures, by_status)
        findings = _extract_findings(result.get("endpoints") or [])
        recommendations = _recommendations(sqli_hits, xss_hits, failures, by_status)

        return ScanAnalysis(
            summary=AnalysisSummary(
                scan_id=scan.get("_id"),
                status=scan.get("status"),
                swagger_title=scan.get("swagger_title"),
                swagger_version=scan.get("swagger_version"),
                base_url=scan.get("base_url"),
                total_requests=total_requests,
                total_failures=failures,
                avg_response_ms=avg_response_ms,
                risk_level=risk_level,
            ),
            indicators=AnalysisIndicators(
                sqli_error_hint=sqli_hits,
                xss_reflected=xss_hits,
                status_5xx=_count_5xx(by_status),
            ),
            findings=findings,
            recommendations=recommendations,
        )


def _count_5xx(by_status: Dict[str, int]) -> int:
    total = 0
    for code, count in by_status.items():
        try:
            if 500 <= int(code) <= 599:
                total += int(count)
        except Exception:
            continue
    return total


def _risk_level(sqli_hits: int, xss_hits: int, failures: int, by_status: Dict[str, int]) -> str:
    if sqli_hits > 0 or xss_hits > 0:
        return "high"
    if _count_5xx(by_status) > 0 or failures > 0:
        return "medium"
    return "low"


def _extract_findings(endpoints: List[Dict[str, Any]]) -> List[AnalysisFinding]:
    findings: List[AnalysisFinding] = []
    for ep in endpoints:
        results = ep.get("results") or []
        indicators = [r for r in results if (r.get("indicators") or {})]
        if not indicators:
            continue
        findings.append(
            AnalysisFinding(
                method=ep.get("method"),
                path=ep.get("path"),
                full_url=ep.get("full_url"),
                indicator_samples=[
                    {
                        "payload_type": r.get("payload_type"),
                        "location": r.get("location"),
                        "status_code": r.get("status_code"),
                        "indicators": r.get("indicators"),
                        "evidence": r.get("evidence"),
                    }
                    for r in indicators[:5]
                ],
            )
        )
    return findings


def _recommendations(sqli_hits: int, xss_hits: int, failures: int, by_status: Dict[str, int]) -> List[str]:
    recs: List[str] = []
    if sqli_hits > 0:
        recs.append("Usar consultas parametrizadas y validar/sanitizar entradas en el backend.")
        recs.append("Evitar exponer errores SQL en respuestas; usar mensajes genéricos.")
    if xss_hits > 0:
        recs.append("Aplicar encoding/sanitización de salida y validar entradas.")
        recs.append("Configurar Content Security Policy (CSP).")
    if _count_5xx(by_status) > 0 or failures > 0:
        recs.append("Revisar manejo de errores y tiempos de respuesta.")
    if not recs:
        recs.append("No se detectaron indicios fuertes; continuar con pruebas más profundas y autenticadas.")
    return recs

