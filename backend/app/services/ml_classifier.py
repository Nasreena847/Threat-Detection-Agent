import json
import logging
import pickle
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import tldextract

from app.config import settings

try:
    import joblib
except ModuleNotFoundError:  # Allows local tests without model dependencies installed.
    joblib = None

try:
    import pandas as pd
except ModuleNotFoundError:  # The model can still be called with a list-of-lists.
    pd = None

logger = logging.getLogger(__name__)
extract_domain = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

COUNT_CHARS = {
    "dot": ".",
    "hyphen": "-",
    "underline": "_",
    "slash": "/",
    "questionmark": "?",
    "equal": "=",
    "at": "@",
    "and": "&",
    "exclamation": "!",
    "space": " ",
    "tilde": "~",
    "comma": ",",
    "plus": "+",
    "asterisk": "*",
    "hashtag": "#",
    "dollar": "$",
    "percent": "%",
}

URL_SHORTENERS = {
    "bit.ly",
    "buff.ly",
    "cutt.ly",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "rebrand.ly",
    "shorturl.at",
    "t.co",
    "tinyurl.com",
}


def _clamp_score(score: int) -> int:
    return max(0, min(score, 100))


def _is_ip_hostname(hostname: str) -> bool:
    parts = hostname.split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def _registered_domain(extracted) -> str:
    return ".".join(part for part in [extracted.domain, extracted.suffix] if part).lower()


def _count_tld_mentions(value: str, suffix: str) -> int:
    if not suffix:
        return 0
    return value.lower().count(f".{suffix.lower()}")


def _has_email(value: str) -> int:
    return int(bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", value, flags=re.IGNORECASE)))


def _component_counts(prefix: str, value: str) -> dict[str, int]:
    return {f"qty_{name}_{prefix}": value.count(character) for name, character in COUNT_CHARS.items()}


def _filename_from_path(path: str) -> str:
    if not path or path.endswith("/"):
        return ""
    return path.rsplit("/", 1)[-1]


def _directory_from_path(path: str) -> str:
    if not path:
        return ""
    if path.endswith("/"):
        return path
    return path.rsplit("/", 1)[0]


def extract_url_only_features(url: str) -> dict[str, int]:
    """Extract the URL-only feature set used by backend/model/url_only_model.joblib."""

    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    hostname = (parsed.hostname or "").lower()
    extracted = extract_domain(normalized_url)
    registered_domain = _registered_domain(extracted)
    directory = _directory_from_path(parsed.path)
    filename = _filename_from_path(parsed.path)
    params = parsed.query

    features: dict[str, int] = {}
    features.update(_component_counts("url", normalized_url))
    features["qty_tld_url"] = _count_tld_mentions(normalized_url, extracted.suffix)
    features["length_url"] = len(normalized_url)

    features.update(_component_counts("domain", hostname))
    features["qty_vowels_domain"] = sum(character in "aeiou" for character in hostname.lower())
    features["domain_length"] = len(hostname)
    features["domain_in_ip"] = int(_is_ip_hostname(hostname))
    features["server_client_domain"] = int("server" in hostname or "client" in hostname)

    features.update(_component_counts("directory", directory))
    features["directory_length"] = len(directory)

    features.update(_component_counts("file", filename))
    features["file_length"] = len(filename)

    features.update(_component_counts("params", params))
    features["params_length"] = len(params)
    features["tld_present_params"] = int(_count_tld_mentions(params, extracted.suffix) > 0)
    features["qty_params"] = len(parse_qsl(params, keep_blank_values=True))
    features["email_in_url"] = _has_email(normalized_url)
    features["url_shortened"] = int(registered_domain in URL_SHORTENERS or hostname in URL_SHORTENERS)

    return features


class MLClassifierService:
    def __init__(
        self,
        model_path: str,
        manifest_path: str,
        enabled: bool,
        phishing_threshold: float,
        model: object | None = None,
        feature_names: list[str] | None = None,
    ) -> None:
        self._model_path = model_path
        self._manifest_path = manifest_path
        self._enabled = enabled
        self._phishing_threshold = phishing_threshold
        self._model = model
        self._feature_names = feature_names
        self._load_error = ""

    def analyze(self, url: str) -> dict[str, object]:
        if not self._enabled:
            return self._unavailable("ML classifier is disabled.")

        model = self._load_model()
        if model is None:
            return self._unavailable(self._load_error or "ML classifier model is not available.")

        feature_names = self._load_feature_names()
        if not feature_names:
            return self._unavailable(self._load_error or "ML classifier feature list is not available.")

        raw_features = extract_url_only_features(url)
        row = {name: raw_features.get(name, 0) for name in feature_names}
        model_input = pd.DataFrame([row], columns=feature_names) if pd is not None else [list(row.values())]
        try:
            probability = self._predict_phishing_probability(model, model_input)
        except Exception as exc:
            logger.exception("ML classifier prediction failed")
            return self._unavailable(f"ML classifier prediction failed: {exc}")

        score = _clamp_score(round(probability * 100))
        verdict = "phishing-like" if probability >= self._phishing_threshold else "benign-like"

        return {
            "score": score,
            "reasons": [f"Random Forest classifier estimated {score}% phishing probability ({verdict})."],
            "provider": "ml",
            "available": True,
            "probability": probability,
            "threshold": self._phishing_threshold,
            "verdict": verdict,
            "model_path": self._model_path,
            "feature_count": len(feature_names),
        }

    def _unavailable(self, reason: str) -> dict[str, object]:
        return {
            "score": 0,
            "reasons": [reason],
            "provider": "ml",
            "available": False,
        }

    def _load_model(self):
        if self._model is not None:
            return self._model

        path = Path(self._model_path)
        if not path.exists():
            self._load_error = f"ML classifier model was not found at {path}."
            return None

        try:
            self._model = joblib.load(path) if joblib is not None else self._load_pickle(path)
        except Exception as exc:  # pragma: no cover - defensive artifact loading path
            logger.exception("ML classifier model failed to load")
            self._load_error = f"ML classifier model failed to load: {exc}"
            return None

        return self._model

    def _load_pickle(self, path: Path):
        with path.open("rb") as model_file:
            return pickle.load(model_file)

    def _load_feature_names(self) -> list[str]:
        if self._feature_names:
            return self._feature_names

        manifest_path = Path(self._manifest_path)
        if manifest_path.exists():
            with manifest_path.open() as manifest_file:
                manifest = json.load(manifest_file)
            feature_names = manifest.get("url_only_model_features") or manifest.get("feature_names")
            if isinstance(feature_names, list):
                self._feature_names = [str(name) for name in feature_names]
                return self._feature_names

        model_feature_names = getattr(self._model, "feature_names_in_", None)
        if model_feature_names is not None:
            self._feature_names = [str(name) for name in model_feature_names]
            return self._feature_names

        self._load_error = f"ML classifier feature manifest was not found at {manifest_path}."
        return []

    def _predict_phishing_probability(self, model, model_input) -> float:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(model_input)
            row = probabilities[0]
            classes = [str(value).lower() for value in getattr(model, "classes_", [])]
            if "1" in classes:
                return float(row[classes.index("1")])
            if "phishing" in classes:
                return float(row[classes.index("phishing")])
            if "malicious" in classes:
                return float(row[classes.index("malicious")])
            return float(row[-1])

        if hasattr(model, "predict"):
            prediction = model.predict(model_input)[0]
            return 1.0 if str(prediction).lower() in {"1", "true", "phishing", "malicious"} else 0.0

        raise RuntimeError("ML classifier model must implement predict_proba() or predict().")


ml_classifier_service = MLClassifierService(
    model_path=settings.ml_model_path,
    manifest_path=settings.ml_feature_manifest_path,
    enabled=settings.ml_classifier_enabled,
    phishing_threshold=settings.ml_phishing_threshold,
)
