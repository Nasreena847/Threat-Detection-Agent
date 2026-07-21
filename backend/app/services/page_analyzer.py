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

SENSITIVE_ACTION_TERMS = {
    "sign in",
    "signin",
    "log in",
    "login",
    "password",
    "passcode",
    "otp",
    "2fa",
    "verification code",
    "credit card",
    "card number",
    "billing",
    "payment",
    "wallet",
    "seed phrase",
    "recovery phrase",
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
SCRIPT_COUNT_THRESHOLD = 18
IFRAME_COUNT_THRESHOLD = 3
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


def _safe_count(value: int | None, fallback: int = 0) -> int:
    return max(0, int(value if value is not None else fallback))


def analyze_page(
    url: str,
    title: str,
    page_text: str,
    html: str,
    forms: int | None = None,
    scripts: int | None = None,
    password_fields: int | None = None,
    iframes: int | None = None,
) -> dict[str, object]:
    """Analyze page content supplied by the extension without fetching the site."""

    score = 0
    reasons: list[str] = []
    combined_text = f"{title}\n{page_text}\n{_strip_html(html)}".lower()
    html_lower = html.lower()
    domain = _registered_domain(url)
    form_count = _safe_count(forms, len(re.findall(r"<form\b", html_lower)))
    password_field_count = _safe_count(
        password_fields,
        len(re.findall(r"type\s*=\s*[\"']?password[\"']?", html_lower)),
    )
    iframe_count = _safe_count(iframes, len(re.findall(r"<iframe\b", html_lower)))
    script_count = _safe_count(scripts, len(re.findall(r"<script\b", html_lower)))
    sensitive_terms = [term for term in sorted(SENSITIVE_ACTION_TERMS) if term in combined_text]

    for phrase in sorted(PHISHING_PHRASES):
        if phrase in combined_text:
            score += 8
            reasons.append(f"Detected phishing phrase: '{phrase}'.")

    for phrase in sorted(URGENT_LANGUAGE):
        if phrase in combined_text:
            score += 5
            reasons.append(f"Detected urgent language: '{phrase}'.")

    if form_count > 0:
        score += min(18, 8 + (form_count * 2))
        reasons.append(f"The page contains {form_count} form(s).")

    if password_field_count > 0:
        score += min(28, 18 + (password_field_count * 3))
        reasons.append(f"The page contains {password_field_count} password field(s).")

    if sensitive_terms:
        score += min(18, 6 + (len(sensitive_terms) * 3))
        reasons.append(f"Detected sensitive action terms: {', '.join(sensitive_terms[:4])}.")

    if form_count > 0 and sensitive_terms:
        score += 12
        reasons.append("The page combines forms with credential, payment, or verification language.")

    if re.search(r"<iframe[^>]+(display\s*:\s*none|visibility\s*:\s*hidden|width=[\"']?0|height=[\"']?0)", html_lower):
        score += 18
        reasons.append("The page contains a hidden iframe.")

    if iframe_count > IFRAME_COUNT_THRESHOLD:
        score += 8
        reasons.append(f"The page embeds {iframe_count} iframes.")

    for pattern, reason in SUSPICIOUS_JS_PATTERNS.items():
        if pattern in html_lower:
            score += 8
            reasons.append(reason)

    external_scripts = _count_external_scripts(html)
    if external_scripts > EXTERNAL_SCRIPT_THRESHOLD:
        score += 12
        reasons.append(f"The page loads {external_scripts} external scripts.")

    if script_count > SCRIPT_COUNT_THRESHOLD:
        score += 8
        reasons.append(f"The page includes {script_count} script elements.")

    for brand, official_domains in BRAND_DOMAINS.items():
        if brand in combined_text and domain not in official_domains:
            score += 12
            reasons.append(f"The page references '{brand}' but is not hosted on an official domain.")

    if any(term in combined_text for term in {"captcha", "verify you are human", "human verification"}) and form_count > 0:
        score += 8
        reasons.append("The page requests verification while collecting form input.")

    if html and len(_strip_html(html)) < 50 and not page_text.strip():
        score += 8
        reasons.append("Very little readable page content was detected.")

    if not reasons:
        reasons.append("No obvious page-level phishing indicators were detected.")

    return {"score": _clamp_score(score), "reasons": reasons}
