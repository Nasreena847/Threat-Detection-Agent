import json
import logging
from typing import Any

from app.config import settings
from app.services.explanation import generate_explanation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You write concise browser-security explanations for TrustTab.
Use only the supplied deterministic audit data. Do not invent facts, vendors,
network calls, malware names, or page behavior. Do not change the risk score,
risk level, or recommendation. Return only valid JSON with keys:
summary, recommendation, source."""


def _safe_json_from_model(content: str) -> dict[str, str]:
    cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    return {
        "summary": str(data.get("summary") or "").strip(),
        "recommendation": str(data.get("recommendation") or "").strip(),
        "source": str(data.get("source") or "groq").strip(),
    }


class LLMExplanationService:
    def __init__(
        self,
        enabled: bool,
        api_key: str,
        model: str,
        timeout_seconds: float,
        fallback_enabled: bool,
    ) -> None:
        self._enabled = enabled
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._fallback_enabled = fallback_enabled

    @property
    def is_configured(self) -> bool:
        return bool(self._enabled and self._api_key)

    def generate(self, risk_result: dict[str, object]) -> dict[str, object]:
        if not self._enabled:
            return self._fallback_or_raise(risk_result, "Groq explanations are disabled.")

        if not self._api_key:
            return self._fallback_or_raise(risk_result, "GROQ_API_KEY is required for LLM explanations.")

        try:
            from groq import Groq
        except ModuleNotFoundError:
            return self._fallback_or_raise(risk_result, "Groq SDK is not installed.")

        try:
            client = Groq(api_key=self._api_key, timeout=self._timeout_seconds)
            response = client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_prompt(risk_result)},
                ],
            )
            content = response.choices[0].message.content or "{}"
            generated = _safe_json_from_model(content)
        except Exception as exc:
            logger.warning("Groq explanation generation failed: %s", exc)
            return self._fallback_or_raise(risk_result, "Groq explanation generation failed.")

        if not generated["summary"]:
            return self._fallback_or_raise(risk_result, "Groq returned an empty summary.")

        return {
            "explanation": generated["summary"][:900],
            "recommendation": generated["recommendation"][:280] or str(risk_result["recommendation"]),
            "source": generated["source"] or "groq",
            "available": True,
            "model": self._model,
        }

    def _fallback_or_raise(self, risk_result: dict[str, object], error: str) -> dict[str, object]:
        if not self._fallback_enabled:
            raise RuntimeError(error)

        return {
            "explanation": generate_explanation(risk_result),
            "recommendation": str(risk_result["recommendation"]),
            "source": "deterministic",
            "available": False,
            "error": error,
        }

    def _build_prompt(self, risk_result: dict[str, object]) -> str:
        reasons = [str(reason) for reason in risk_result.get("reasons", [])][:8]
        payload: dict[str, Any] = {
            "risk_score": int(risk_result["risk_score"]),
            "risk_level": str(risk_result["risk_level"]),
            "recommendation": str(risk_result["recommendation"]),
            "components": risk_result.get("components", {}),
            "threat_intel": risk_result.get("threat_intel", {}),
            "ml": risk_result.get("ml", {}),
            "evidence": reasons,
            "instructions": (
                "Write 2-4 plain-language sentences. Explain the most important evidence, "
                "keep the same risk score and risk level, and keep advice practical."
            ),
        }
        return json.dumps(payload)


llm_explanation_service = LLMExplanationService(
    enabled=settings.llm_explanations_enabled,
    api_key=settings.groq_api_key,
    model=settings.groq_model,
    timeout_seconds=settings.groq_timeout_seconds,
    fallback_enabled=settings.deterministic_explanation_fallback_enabled,
)
