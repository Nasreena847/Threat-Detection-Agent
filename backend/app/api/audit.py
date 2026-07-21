import threading
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import settings
from app.schemas.request import AuditRequest
from app.schemas.response import AuditResponse, CrooAuditResponse
from app.services.audit_pipeline import run_audit_pipeline

router = APIRouter(prefix="/api/audit", tags=["Audit"])
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
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AuditResponse(
        url=str(result["url"]),
        risk_score=int(result["risk_score"]),
        risk_level=str(result["risk_level"]),
        reasons=[str(reason) for reason in result["reasons"]],
        recommendation=str(result["recommendation"]),
        explanation=str(result["explanation"]),
        evidence=[str(reason) for reason in result["reasons"]],
        threat_intel=result["threat_intel"] if isinstance(result.get("threat_intel"), dict) else {},
        croo=CrooAuditResponse(agent_used=False, response=None),
    )
