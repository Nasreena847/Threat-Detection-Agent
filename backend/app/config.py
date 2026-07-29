import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Threat Detection Agent")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", os.getenv("TRUSTTAB_EXTENSION_ORIGIN", "")).split(",")
        if origin.strip()
    )
    audit_api_key: str = os.getenv("AUDIT_API_KEY", "").strip()
    audit_rate_limit_per_minute: int = int(os.getenv("AUDIT_RATE_LIMIT_PER_MINUTE", "60"))
    virustotal_api_key: str = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
    virustotal_timeout_seconds: float = float(os.getenv("VIRUSTOTAL_TIMEOUT_SECONDS", "3"))
    virustotal_cache_ttl_seconds: int = int(os.getenv("VIRUSTOTAL_CACHE_TTL_SECONDS", "3600"))
    virustotal_submit_unknown_urls: bool = _env_bool("VIRUSTOTAL_SUBMIT_UNKNOWN_URLS")
    dns_reputation_enabled: bool = _env_bool("DNS_REPUTATION_ENABLED", True)
    dns_timeout_seconds: float = float(os.getenv("DNS_TIMEOUT_SECONDS", "2"))


settings = Settings()
