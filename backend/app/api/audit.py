import logging
import threading
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import settings
from app.schemas.request import AuditRequest
from app.schemas.response import AuditResponse, CrooAuditResponse, ScanHistoryItem, ScanHistoryResponse
from app.services.audit_pipeline import run_audit_pipeline
from app.services.scan_history import scan_history_store

router = APIRouter(prefix="/api/audit", tags=["Audit"])
logger = logging.getLogger(__name__)
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_lock = threading.Lock()
_rate_limit_buckets: dict[str, Deque[float]] = defaultdict(deque)


def _client_key(http_request: Request | None) -> str:
    if http_request is None or http_request.client is None:
        return "direct-call"

    forwarded_for = http_request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    return http_request.client.host


def _enforce_rate_limit(http_request: Request | None) -> None:
    limit = settings.audit_rate_limit_per_minute
    if limit <= 0 or http_request is None:
        return

    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    client_key = _client_key(http_request)

    with _rate_limit_lock:
        bucket = _rate_limit_buckets[client_key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Audit rate limit exceeded. Please retry shortly.",
            )

        bucket.append(now)


def _enforce_audit_api_key(x_trusttab_api_key: str | None, x_api_key: str | None) -> None:
    expected_key = settings.audit_api_key
    if not expected_key:
        return

    supplied_key = next((value for value in (x_trusttab_api_key, x_api_key) if isinstance(value, str)), "")
    if supplied_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid audit API key.",
        )


@router.post("", response_model=AuditResponse)
@router.post("/", response_model=AuditResponse, include_in_schema=False)
def audit(
    request: AuditRequest,
    http_request: Request = None,
    x_trusttab_api_key: str | None = Header(default=None, alias="X-TrustTab-API-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> AuditResponse:
    """Run the complete deterministic audit pipeline for the active browser tab."""

    _enforce_audit_api_key(x_trusttab_api_key, x_api_key)
    _enforce_rate_limit(http_request)

    try:
        result = run_audit_pipeline(
            url=request.url,
            title=request.title,
            page_text=request.page_text or "",
            html=request.html or "",
            forms=request.forms,
            scripts=request.scripts,
            password_fields=request.password_fields,
            iframes=request.iframes,
            ads=request.ads,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    scan_id = None
    try:
        scan_id = scan_history_store.save(result)
    except Exception:
        logger.exception("Failed to save audit scan history")

    return AuditResponse(
        scan_id=scan_id,
        url=str(result["url"]),
        risk_score=int(result["risk_score"]),
        risk_level=str(result["risk_level"]),
        reasons=[str(reason) for reason in result["reasons"]],
        recommendation=str(result["recommendation"]),
        explanation=str(result["explanation"]),
        explanation_source=result["explanation_source"] if isinstance(result.get("explanation_source"), dict) else {},
        evidence=[str(reason) for reason in result["reasons"]],
        ad_risk=result["ad_risk"] if isinstance(result.get("ad_risk"), dict) else {},
        threat_intel=result["threat_intel"] if isinstance(result.get("threat_intel"), dict) else {},
        ml=result["ml"] if isinstance(result.get("ml"), dict) else {},
        croo=CrooAuditResponse(agent_used=False, response=None),
    )


@router.get("/history", response_model=ScanHistoryResponse)
def audit_history(limit: int = 50, domain: str | None = None) -> ScanHistoryResponse:
    scans = scan_history_store.list_recent(limit=limit, domain=domain)
    return ScanHistoryResponse(scans=[ScanHistoryItem(**scan) for scan in scans])


@router.get("/history/{scan_id}", response_model=ScanHistoryItem)
def audit_history_item(scan_id: int) -> ScanHistoryItem:
    scan = scan_history_store.get(scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan history item not found.")

    return ScanHistoryItem(**scan)


@router.delete("/history", response_model=dict[str, int])
def clear_audit_history() -> dict[str, int]:
    return {"deleted": scan_history_store.clear()}
