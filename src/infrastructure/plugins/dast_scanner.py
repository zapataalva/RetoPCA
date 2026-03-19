import argparse
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.infrastructure.plugins.payloads import PAYLOADS

SQLI_ERROR_HINTS = ["sql", "syntax", "mysql", "psql", "sqlite", "ora-"]
MAX_EVIDENCE_CHARS = 300


def _build_body_from_schema(schema: Dict[str, Any], payload: str) -> Dict[str, Any]:
    if not schema:
        return {"input": payload}
    if "properties" in schema:
        body: Dict[str, Any] = {}
        for k, v in schema["properties"].items():
            if v.get("type") == "string":
                body[k] = payload
            elif v.get("type") == "integer":
                body[k] = 1
            elif v.get("type") == "number":
                body[k] = 1.0
            elif v.get("type") == "boolean":
                body[k] = True
            else:
                body[k] = payload
        return body
    return {"input": payload}


def _sample_value(param: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Any:
    if overrides:
        defaults = overrides.get("param_defaults") or {}
        name = param.get("name")
        if name in defaults:
            return defaults[name]
    if "default" in param:
        return param["default"]
    ptype = param.get("type")
    if ptype == "integer":
        return 1
    if ptype == "number":
        return 1.0
    if ptype == "boolean":
        return True
    if ptype == "array":
        items = param.get("items") or {}
        return [_sample_value(items)]
    return "test"


def _apply_path_params(path: str, path_params: List[Dict[str, Any]], overrides: Optional[Dict[str, Any]]) -> str:
    for p in path_params:
        name = p.get("name")
        if not name:
            continue
        value = _sample_value(p, overrides)
        path = path.replace("{" + name + "}", str(value))
    return path


def _normalize_base_url(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    if base_url.startswith("http://") or base_url.startswith("https://"):
        return base_url
    return f"https://{base_url.lstrip('/')}"


def _extract_base_url(spec: Dict[str, Any]) -> Optional[str]:
    # Swagger/OpenAPI v2
    host = spec.get("host")
    base_path = spec.get("basePath") or ""
    schemes = spec.get("schemes") or []
    if host:
        scheme = schemes[0] if schemes else "https"
        return _normalize_base_url(f"{scheme}://{host}{base_path}")

    # OpenAPI v3
    servers = spec.get("servers") or []
    if servers:
        return _normalize_base_url(servers[0].get("url"))
    return None


def _extract_swagger_info(spec: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    info = spec.get("info") or {}
    return info.get("title"), info.get("version")


async def _call_endpoint(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    params: Dict[str, Any],
    json_body: Optional[Dict[str, Any]],
    data_body: Optional[Dict[str, Any]],
    files_body: Optional[Dict[str, Any]],
    headers: Optional[Dict[str, str]],
) -> Tuple[Optional[int], Optional[float], Optional[int], Optional[str], str]:
    start = time.perf_counter()
    try:
        resp = await client.request(
            method,
            url,
            params=params or None,
            json=json_body,
            data=data_body,
            files=files_body,
            headers=headers,
        )
        elapsed = (time.perf_counter() - start) * 1000
        size = len(resp.content) if resp.content is not None else 0
        return resp.status_code, elapsed, size, None, resp.text
    except Exception as exc:  # noqa: BLE001
        elapsed = (time.perf_counter() - start) * 1000
        return None, elapsed, None, str(exc), ""


async def run_scan(swagger_path: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    with open(swagger_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    base_url = _extract_base_url(spec)
    title, version = _extract_swagger_info(spec)

    endpoints: List[Dict[str, Any]] = []
    total_requests = 0
    total_failures = 0
    total_resp_time = 0.0
    by_status: Dict[str, int] = {}
    by_payload_type: Dict[str, int] = {}
    indicators_summary: Dict[str, int] = {}

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        paths = spec.get("paths") or {}
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                params_def = details.get("parameters") or []
                path_params = [p for p in params_def if p.get("in") == "path"]
                path_with_values = _apply_path_params(path, path_params, overrides)
                full_url = f"{base_url.rstrip('/')}{path_with_values}" if base_url else path_with_values
                query_params = [p for p in params_def if p.get("in") == "query"]
                form_params = [p for p in params_def if p.get("in") == "formData"]
                body_schema = None
                body_param = next((p for p in params_def if p.get("in") == "body"), None)
                if body_param and body_param.get("schema"):
                    body_schema = body_param.get("schema") or {}

                endpoint_results: List[Dict[str, Any]] = []

                for payload_group in PAYLOADS:
                    ptype = payload_group["type"]
                    by_payload_type.setdefault(ptype, 0)

                    for payload in payload_group["items"]:
                        params = {}
                        json_body = None
                        data_body = None
                        files_body = None
                        headers = None
                        location = "query"

                        if query_params:
                            for qp in query_params:
                                params[qp.get("name") or "q"] = payload
                        elif form_params:
                            data_body = {}
                            files_body = {}
                            for fp in form_params:
                                name = fp.get("name") or "file"
                                fptype = fp.get("type")
                                if fptype == "file":
                                    file_defaults = (overrides or {}).get("file_defaults") or {}
                                    fdef = file_defaults.get(name)
                                    if isinstance(fdef, dict):
                                        filename = fdef.get("filename", "test.txt")
                                        content = fdef.get("content", "test")
                                        if isinstance(content, str):
                                            content = content.encode("utf-8")
                                        content_type = fdef.get("content_type", "text/plain")
                                        files_body[name] = (filename, content, content_type)
                                    else:
                                        files_body[name] = ("test.txt", b"test", "text/plain")
                                else:
                                    data_body[name] = payload if fptype == "string" else _sample_value(fp, overrides)
                            headers = {"Content-Type": "multipart/form-data"}
                            location = "formData"
                        elif body_schema is not None:
                            json_body = _build_body_from_schema(body_schema, payload)
                            location = "body"
                        else:
                            params["q"] = payload

                        status, elapsed, size, error, text = await _call_endpoint(
                            client, method, full_url, params, json_body, data_body, files_body, headers
                        )
                        total_requests += 1
                        by_payload_type[ptype] += 1
                        if status is None:
                            total_failures += 1
                        if elapsed is not None:
                            total_resp_time += elapsed

                        if status is not None:
                            key = str(status)
                            by_status[key] = by_status.get(key, 0) + 1

                        indicators: Dict[str, Any] = {}
                        if ptype == "xss" and payload in text:
                            indicators["xss_reflected"] = True
                            indicators_summary["xss_reflected"] = indicators_summary.get("xss_reflected", 0) + 1
                        if ptype == "sqli":
                            low = text.lower()
                            if any(h in low for h in SQLI_ERROR_HINTS) or (status and status >= 500):
                                indicators["sqli_error_hint"] = True
                                indicators_summary["sqli_error_hint"] = indicators_summary.get("sqli_error_hint", 0) + 1

                        evidence = text[:MAX_EVIDENCE_CHARS] if error else ""
                        endpoint_results.append(
                            {
                                "payload": payload,
                                "payload_type": ptype,
                                "location": location,
                                "status_code": status,
                                "response_time_ms": elapsed,
                                "response_size": size,
                                "error": error,
                                "evidence": evidence,
                                "indicators": indicators,
                            }
                        )

                endpoints.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "full_url": full_url,
                        "params": {"query": [p.get("name") for p in query_params]},
                        "body": {"schema": body_schema} if body_schema else None,
                        "results": endpoint_results,
                    }
                )

    avg_response = round(total_resp_time / total_requests, 2) if total_requests else 0.0
    metrics = {
        "total_endpoints": len(endpoints),
        "total_requests": total_requests,
        "total_failures": total_failures,
        "avg_response_ms": avg_response,
        "by_status_code": by_status,
        "by_payload_type": by_payload_type,
        "indicators_summary": indicators_summary,
    }

    return {
        "status": "completed",
        "swagger_title": title,
        "swagger_version": version,
        "base_url": base_url,
        "endpoints": endpoints,
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swagger", required=True)
    args = parser.parse_args()

    result = asyncio.run(run_scan(args.swagger))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()


class DastScannerRunner:
    async def run(self, swagger_path: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await run_scan(swagger_path, overrides)
