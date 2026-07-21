import base64
import logging
import threading
import time
from urllib.parse import urlparse

import httpx
import tldextract

from app.config import settings

KNOWN_TRUSTED_DOMAINS = {
    "google.com",
    "github.com",
    "microsoft.com",
    "apple.com",
    "amazon.com",
    "cloudflare.com",
    "wikipedia.org",
}

HIGH_RISK_TERMS = {
    "phish",
    "malware",
    "free-crypto",
    "airdrop",
    "wallet-verify",
    "account-restore",
}
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
logger = logging.getLogger(__name__)


def _clamp_score(score: int) -> int:
    return max(0, min(score, 100))


def _virustotal_url_id(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def _score_virustotal_stats(stats: dict[str, object]) -> int:
    malicious = int(stats.get("malicious") or 0)
    suspicious = int(stats.get("suspicious") or 0)
    harmless = int(stats.get("harmless") or 0)
    undetected = int(stats.get("undetected") or 0)
    total = malicious + suspicious + harmless + undetected

    if total <= 0:
        return 0

    weighted_detections = (malicious * 18) + (suspicious * 9)
    ratio_boost = round(((malicious + suspicious) / total) * 55)
    return _clamp_score(weighted_detections + ratio_boost)


def _reason_from_virustotal_stats(stats: dict[str, object]) -> str:
    malicious = int(stats.get("malicious") or 0)
    suspicious = int(stats.get("suspicious") or 0)
    harmless = int(stats.get("harmless") or 0)
    undetected = int(stats.get("undetected") or 0)

    if malicious or suspicious:
        return (
            "VirusTotal threat intelligence reported "
            f"{malicious} malicious and {suspicious} suspicious vendor detections."
        )

    if harmless:
        return f"VirusTotal threat intelligence reported no malicious detections across {harmless + undetected} vendors."

    return "VirusTotal threat intelligence returned no vendor detection summary for this URL."


class VirusTotalClient:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float,
        cache_ttl_seconds: int,
        submit_unknown_urls: bool,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._submit_unknown_urls = submit_unknown_urls
        self._cache_lock = threading.Lock()
        self._cache: dict[str, tuple[float, dict[str, object]]] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def analyze_url(self, url: str) -> dict[str, object] | None:
        if not self.is_configured:
            return None

        cached_result = self._read_cache(url)
        if cached_result is not None:
            return {**cached_result, "cache": "hit"}

        result = self._fetch_url_report(url)
        self._write_cache(url, result)
        return {**result, "cache": "miss"}

    def _read_cache(self, url: str) -> dict[str, object] | None:
        if self._cache_ttl_seconds <= 0:
            return None

        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(url)
            if cached is None:
                return None

            expires_at, result = cached
            if expires_at <= now:
                self._cache.pop(url, None)
                return None

            return result.copy()

    def _write_cache(self, url: str, result: dict[str, object]) -> None:
        if self._cache_ttl_seconds <= 0:
            return

        expires_at = time.monotonic() + self._cache_ttl_seconds
        with self._cache_lock:
            self._cache[url] = (expires_at, result.copy())

    def _fetch_url_report(self, url: str) -> dict[str, object]:
        url_id = _virustotal_url_id(url)
        try:
            response = httpx.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers={"x-apikey": self._api_key},
                timeout=self._timeout_seconds,
            )
        except httpx.HTTPError as exc:
            logger.warning("VirusTotal URL lookup failed: %s", exc)
            return {
                "score": 0,
                "reasons": ["VirusTotal threat intelligence lookup was unavailable."],
                "provider": "virustotal",
                "available": False,
            }

        if response.status_code == 404:
            submitted = self._submit_url_for_analysis(url) if self._submit_unknown_urls else None
            return {
                "score": 0,
                "reasons": [
                    "VirusTotal has no existing report for this URL."
                    if submitted is None
                    else "VirusTotal has no existing report for this URL, so it was submitted for analysis."
                ],
                "provider": "virustotal",
                "available": True,
                "submitted": submitted is not None,
                "analysis_id": submitted.get("analysis_id") if submitted else None,
            }

        if response.status_code in {401, 403, 429}:
            logger.warning("VirusTotal URL lookup returned status %s", response.status_code)
            return {
                "score": 0,
                "reasons": ["VirusTotal threat intelligence lookup was rate-limited or unauthorized."],
                "provider": "virustotal",
                "available": False,
            }

        if response.status_code >= 400:
            logger.warning("VirusTotal URL lookup returned status %s", response.status_code)
            return {
                "score": 0,
                "reasons": ["VirusTotal threat intelligence lookup failed."],
                "provider": "virustotal",
                "available": False,
            }

        payload = response.json()
        attributes = payload.get("data", {}).get("attributes", {})
        stats = attributes.get("last_analysis_stats", {})
        if not isinstance(stats, dict):
            stats = {}

        return {
            "score": _score_virustotal_stats(stats),
            "reasons": [_reason_from_virustotal_stats(stats)],
            "provider": "virustotal",
            "available": True,
            "submitted": False,
            "stats": stats,
            "reputation": attributes.get("reputation"),
            "last_analysis_date": attributes.get("last_analysis_date"),
            "permalink": payload.get("data", {}).get("links", {}).get("self"),
        }

    def _submit_url_for_analysis(self, url: str) -> dict[str, object] | None:
        try:
            response = httpx.post(
                "https://www.virustotal.com/api/v3/urls",
                headers={"x-apikey": self._api_key},
                data={"url": url},
                timeout=self._timeout_seconds,
            )
        except httpx.HTTPError as exc:
            logger.warning("VirusTotal URL submission failed: %s", exc)
            return None

        if response.status_code >= 400:
            logger.warning("VirusTotal URL submission returned status %s", response.status_code)
            return None

        payload = response.json()
        data = payload.get("data", {})
        return {
            "analysis_id": data.get("id"),
            "type": data.get("type"),
        }


class ReputationService:
    """Abstraction for domain reputation providers.

    Uses deterministic local checks by default and enriches with VirusTotal
    threat intelligence when VIRUSTOTAL_API_KEY is configured.
    """

    def __init__(self, virustotal_client: VirusTotalClient | None = None) -> None:
        self._virustotal_client = virustotal_client or VirusTotalClient(
            settings.virustotal_api_key,
            settings.virustotal_timeout_seconds,
            settings.virustotal_cache_ttl_seconds,
            settings.virustotal_submit_unknown_urls,
        )

    def analyze(self, url: str) -> dict[str, object]:
        local_result = self._analyze_local(url)
        virustotal_result = self._virustotal_client.analyze_url(url)
        if virustotal_result is None:
            return local_result

        return self._merge_results(local_result, virustotal_result)

    def _analyze_local(self, url: str) -> dict[str, object]:
        parsed = urlparse(url)
        extracted = extract_domain(url)
        registered_domain = ".".join(
            part for part in [extracted.domain, extracted.suffix] if part
        ).lower()
        normalized_url = url.lower()

        score = 8
        reasons: list[str] = ["Deterministic reputation check completed."]

        if registered_domain in KNOWN_TRUSTED_DOMAINS:
            return {
                "score": 0,
                "reasons": [f"Domain reputation appears trusted for {registered_domain}."],
                "provider": "local",
            }

        for term in sorted(HIGH_RISK_TERMS):
            if term in normalized_url:
                score += 20
                reasons.append(f"Local reputation analysis found high-risk term '{term}' in the URL.")

        if parsed.hostname and parsed.hostname.count("-") >= 3:
            score += 10
            reasons.append("Domain contains multiple hyphens, a common phishing pattern.")

        return {"score": min(score, 100), "reasons": reasons, "provider": "local"}

    def _merge_results(self, local_result: dict[str, object], virustotal_result: dict[str, object]) -> dict[str, object]:
        local_score = int(local_result.get("score", 0))
        virustotal_score = int(virustotal_result.get("score", 0))
        score = max(local_score, virustotal_score)

        if virustotal_score >= 45:
            score = max(score, round((local_score * 0.25) + (virustotal_score * 0.75)))

        return {
            "score": _clamp_score(score),
            "reasons": [*self._reasons(local_result), *self._reasons(virustotal_result)],
            "provider": "local+virustotal",
            "virustotal": {
                "available": bool(virustotal_result.get("available")),
                "cache": virustotal_result.get("cache"),
                "submitted": bool(virustotal_result.get("submitted")),
                "analysis_id": virustotal_result.get("analysis_id"),
                "score": virustotal_score,
                "stats": virustotal_result.get("stats", {}),
                "reputation": virustotal_result.get("reputation"),
                "last_analysis_date": virustotal_result.get("last_analysis_date"),
                "permalink": virustotal_result.get("permalink"),
            },
        }

    def _reasons(self, result: dict[str, object]) -> list[str]:
        reasons = result.get("reasons", [])
        return [str(reason) for reason in reasons] if isinstance(reasons, list) else []


reputation_service = ReputationService()
