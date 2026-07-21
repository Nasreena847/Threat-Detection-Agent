import base64
import logging
import threading
import time
from urllib.parse import urlparse

import httpx
import tldextract

from app.config import settings

try:
    import dns.exception
    import dns.resolver
except ModuleNotFoundError:  # DNS reputation is optional in lean local environments.
    dns = None

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


def _registered_domain(url: str) -> str:
    extracted = extract_domain(url)
    return ".".join(part for part in [extracted.domain, extracted.suffix] if part).lower()


def _hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower().strip(".")


def _is_private_dns_ip(value: str) -> bool:
    try:
        import ipaddress

        ip_address = ipaddress.ip_address(value)
    except ValueError:
        return False

    return (
        ip_address.is_private
        or ip_address.is_loopback
        or ip_address.is_link_local
        or ip_address.is_reserved
        or ip_address.is_unspecified
    )


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


class DNSReputationClient:
    def __init__(self, enabled: bool, timeout_seconds: float) -> None:
        self._enabled = enabled
        self._timeout_seconds = timeout_seconds

    def analyze_url(self, url: str) -> dict[str, object] | None:
        if not self._enabled:
            return None

        if dns is None:
            return {
                "score": 0,
                "reasons": ["DNS reputation checks are unavailable because dnspython is not installed."],
                "provider": "dns",
                "available": False,
            }

        hostname = _hostname(url)
        registered_domain = _registered_domain(url)
        if not hostname:
            return {
                "score": 15,
                "reasons": ["DNS reputation could not inspect the URL because no hostname was present."],
                "provider": "dns",
                "available": True,
                "records": {},
            }

        resolver = dns.resolver.Resolver()
        resolver.timeout = self._timeout_seconds
        resolver.lifetime = self._timeout_seconds

        records = {
            "a": self._resolve_records(resolver, hostname, "A"),
            "aaaa": self._resolve_records(resolver, hostname, "AAAA"),
            "mx": self._resolve_records(resolver, registered_domain, "MX"),
            "ns": self._resolve_records(resolver, registered_domain, "NS"),
            "txt": self._resolve_records(resolver, registered_domain, "TXT"),
        }

        if not any(records.values()):
            return {
                "score": 0,
                "reasons": ["DNS reputation lookup returned no records and was treated as unavailable."],
                "provider": "dns",
                "available": False,
                "records": records,
            }

        score = 0
        reasons: list[str] = []
        address_records = [*records["a"], *records["aaaa"]]

        if not address_records:
            score += 18
            reasons.append("DNS check found no A or AAAA records for the hostname.")

        private_addresses = [address for address in address_records if _is_private_dns_ip(address)]
        if private_addresses:
            score += 35
            reasons.append("DNS check resolved the hostname to private, local, or reserved address space.")

        if not records["ns"]:
            score += 12
            reasons.append("DNS check found no nameserver records for the registered domain.")
        elif len(records["ns"]) == 1:
            score += 5
            reasons.append("DNS check found only one nameserver, which reduces resilience.")

        if not records["mx"]:
            reasons.append("DNS check found no MX records; this is acceptable for some sites but lowers domain context.")

        if len(set(address_records)) >= 4:
            reasons.append("DNS check found multiple public address records, which is common for established services.")

        if not reasons:
            reasons.append("DNS reputation checks found normal public DNS records.")

        return {
            "score": _clamp_score(score),
            "reasons": reasons,
            "provider": "dns",
            "available": True,
            "records": records,
        }

    def _resolve_records(self, resolver, name: str, record_type: str) -> list[str]:
        if not name:
            return []

        try:
            answers = resolver.resolve(name, record_type)
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
        ):
            return []
        except Exception as exc:  # pragma: no cover - defensive resolver path
            logger.warning("DNS lookup failed for %s %s: %s", name, record_type, exc)
            return []

        values: list[str] = []
        for answer in answers:
            if record_type == "MX":
                exchange = getattr(answer, "exchange", "")
                values.append(str(exchange).rstrip("."))
            elif record_type == "TXT":
                strings = getattr(answer, "strings", [])
                values.append(" ".join(part.decode(errors="ignore") for part in strings))
            else:
                values.append(str(answer).rstrip("."))
        return values


class ReputationService:
    """Abstraction for domain reputation providers.

    Uses deterministic local checks by default and enriches with VirusTotal
    threat intelligence when VIRUSTOTAL_API_KEY is configured.
    """

    def __init__(
        self,
        virustotal_client: VirusTotalClient | None = None,
        dns_client: DNSReputationClient | None = None,
    ) -> None:
        self._virustotal_client = virustotal_client or VirusTotalClient(
            settings.virustotal_api_key,
            settings.virustotal_timeout_seconds,
            settings.virustotal_cache_ttl_seconds,
            settings.virustotal_submit_unknown_urls,
        )
        self._dns_client = dns_client or DNSReputationClient(
            settings.dns_reputation_enabled,
            settings.dns_timeout_seconds,
        )

    def analyze(self, url: str) -> dict[str, object]:
        local_result = self._analyze_local(url)
        dns_result = self._dns_client.analyze_url(url)
        virustotal_result = self._virustotal_client.analyze_url(url)
        provider_results = [result for result in (local_result, dns_result, virustotal_result) if result is not None]

        return self._merge_results(provider_results)

    def _analyze_local(self, url: str) -> dict[str, object]:
        parsed = urlparse(url)
        registered_domain = _registered_domain(url)
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

    def _merge_results(self, provider_results: list[dict[str, object]]) -> dict[str, object]:
        scores = {str(result.get("provider")): int(result.get("score", 0)) for result in provider_results}
        local_result = self._result_for_provider(provider_results, "local")
        dns_result = self._result_for_provider(provider_results, "dns")
        virustotal_result = self._result_for_provider(provider_results, "virustotal")
        local_score = int(local_result.get("score", 0)) if local_result else 0
        dns_score = int(dns_result.get("score", 0)) if dns_result else 0
        virustotal_score = int(virustotal_result.get("score", 0)) if virustotal_result else 0
        score = max(scores.values(), default=0)

        if virustotal_score >= 45:
            score = max(score, round((local_score * 0.25) + (virustotal_score * 0.75)))
        if dns_score >= 30 and local_score >= 15:
            score = max(score, round((dns_score * 0.55) + (local_score * 0.45)))

        return {
            "score": _clamp_score(score),
            "reasons": [reason for result in provider_results for reason in self._reasons(result)],
            "provider": "+".join(str(result.get("provider")) for result in provider_results),
            "dns": {
                "available": bool(dns_result.get("available")) if dns_result else False,
                "score": dns_score,
                "records": dns_result.get("records", {}) if dns_result else {},
            },
            "virustotal": {
                "available": bool(virustotal_result.get("available")) if virustotal_result else False,
                "cache": virustotal_result.get("cache") if virustotal_result else None,
                "submitted": bool(virustotal_result.get("submitted")) if virustotal_result else False,
                "analysis_id": virustotal_result.get("analysis_id") if virustotal_result else None,
                "score": virustotal_score,
                "stats": virustotal_result.get("stats", {}) if virustotal_result else {},
                "reputation": virustotal_result.get("reputation") if virustotal_result else None,
                "last_analysis_date": virustotal_result.get("last_analysis_date") if virustotal_result else None,
                "permalink": virustotal_result.get("permalink") if virustotal_result else None,
            },
        }

    def _result_for_provider(self, provider_results: list[dict[str, object]], provider: str) -> dict[str, object] | None:
        for result in provider_results:
            if result.get("provider") == provider:
                return result
        return None

    def _reasons(self, result: dict[str, object]) -> list[str]:
        reasons = result.get("reasons", [])
        return [str(reason) for reason in reasons] if isinstance(reasons, list) else []


reputation_service = ReputationService()
