import re
from html import unescape

import tldextract

PHISHING_PHRASES = {
    "verify your account",
    "confirm your identity",
    "login immediately",
    "update payment",
    "account has been suspended",
    "unusual activity",
    "security alert",
    "restore access",
    "validate your wallet",
    "confirm your password",
}

URGENT_LANGUAGE = {
    "urgent",
    "immediately",
    "limited time",
    "act now",
    "expires today",
    "final warning",
    "last chance",
}

SUSPICIOUS_JS_PATTERNS = {
    "document.location": "JavaScript attempts to modify the browser location.",
    "window.location": "JavaScript attempts to redirect the page.",
    "eval(": "JavaScript uses eval, which can hide malicious behavior.",
    "atob(": "JavaScript decodes obfuscated content.",
    "document.cookie": "JavaScript accesses browser cookies.",
}

BRAND_DOMAINS = {
    "paypal": {"paypal.com"},
    "google": {"google.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com"},
    "apple": {"apple.com"},
    "amazon": {"amazon.com"},
    "facebook": {"facebook.com", "meta.com"},
    "instagram": {"instagram.com"},
    "netflix": {"netflix.com"},
    "binance": {"binance.com"},
    "coinbase": {"coinbase.com"},
}

EXTERNAL_SCRIPT_THRESHOLD = 10
MAX_SCORE = 100
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


def _clamp_score(score: int) -> int:
    return max(0, min(score, MAX_SCORE))


def _strip_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return unescape(re.sub(r"\s+", " ", without_tags)).strip()


def _registered_domain(url: str) -> str:
    extracted = extract_domain(url)
    return ".".join(part for part in [extracted.domain, extracted.suffix] if part).lower()


def _count_external_scripts(html: str) -> int:
    return len(re.findall(r"<script[^>]+src=[\"']?https?://", html, flags=re.IGNORECASE))


def analyze_page(url: str, title: str, page_text: str, html: str) -> dict[str, object]:
    """Analyze page content supplied by the extension without fetching the site."""

    score = 0
    reasons: list[str] = []
    combined_text = f"{title}\n{page_text}\n{_strip_html(html)}".lower()
    html_lower = html.lower()
    domain = _registered_domain(url)

    for phrase in sorted(PHISHING_PHRASES):
        if phrase in combined_text:
            score += 8
            reasons.append(f"Detected phishing phrase: '{phrase}'.")

    for phrase in sorted(URGENT_LANGUAGE):
        if phrase in combined_text:
            score += 5
            reasons.append(f"Detected urgent language: '{phrase}'.")

    if re.search(r"<form\b", html_lower):
        score += 10
        reasons.append("The page contains at least one form.")

    if re.search(r"type\s*=\s*[\"']?password[\"']?", html_lower):
        score += 18
        reasons.append("The page contains a password field.")

    if re.search(r"<iframe[^>]+(display\s*:\s*none|visibility\s*:\s*hidden|width=[\"']?0|height=[\"']?0)", html_lower):
        score += 18
        reasons.append("The page contains a hidden iframe.")

    for pattern, reason in SUSPICIOUS_JS_PATTERNS.items():
        if pattern in html_lower:
            score += 8
            reasons.append(reason)

    external_scripts = _count_external_scripts(html)
    if external_scripts > EXTERNAL_SCRIPT_THRESHOLD:
        score += 12
        reasons.append(f"The page loads {external_scripts} external scripts.")

    for brand, official_domains in BRAND_DOMAINS.items():
        if brand in combined_text and domain not in official_domains:
            score += 12
            reasons.append(f"The page references '{brand}' but is not hosted on an official domain.")

    if html and len(_strip_html(html)) < 50 and not page_text.strip():
        score += 8
        reasons.append("Very little readable page content was detected.")

    if not reasons:
        reasons.append("No obvious page-level phishing indicators were detected.")

    return {"score": _clamp_score(score), "reasons": reasons}
