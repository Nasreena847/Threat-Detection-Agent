import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.llm_explanation import LLMExplanationService, _safe_json_from_model


RISK_RESULT = {
    "risk_score": 72,
    "risk_level": "High",
    "recommendation": "Avoid interacting with this website and do not enter credentials or payment details.",
    "reasons": [
        "The URL does not use HTTPS.",
        "The page contains 1 password field(s).",
        "Random Forest classifier estimated 87% phishing probability (phishing-like).",
    ],
    "components": {"url": 35, "page": 60, "reputation": 8, "ml": 87},
    "threat_intel": {},
    "ml": {"available": True, "score": 87, "probability": 0.87},
}


class FakeMessage:
    content = '{"summary":"High risk because credential collection and URL signals align.","recommendation":"Do not enter credentials.","source":"groq"}'


class FakeChoice:
    message = FakeMessage()


class FakeCompletions:
    def create(self, **_kwargs):
        return type("FakeResponse", (), {"choices": [FakeChoice()]})()


class FakeChat:
    completions = FakeCompletions()


class FakeGroq:
    def __init__(self, **_kwargs) -> None:
        self.chat = FakeChat()


class LLMExplanationTests(unittest.TestCase):
    def test_safe_json_from_model_accepts_fenced_json(self) -> None:
        result = _safe_json_from_model('```json\n{"summary":"Done","recommendation":"Leave","source":"groq"}\n```')

        self.assertEqual(result["summary"], "Done")
        self.assertEqual(result["recommendation"], "Leave")
        self.assertEqual(result["source"], "groq")

    def test_llm_explanation_falls_back_when_not_configured(self) -> None:
        service = LLMExplanationService(
            enabled=True,
            api_key="",
            model="gemma2-9b-it",
            timeout_seconds=4,
            fallback_enabled=True,
        )

        result = service.generate(RISK_RESULT)

        self.assertFalse(result["available"])
        self.assertEqual(result["source"], "deterministic")
        self.assertIn("High", result["explanation"])
        self.assertIn("GROQ_API_KEY", result["error"])

    def test_llm_explanation_raises_when_fallback_is_disabled(self) -> None:
        service = LLMExplanationService(
            enabled=True,
            api_key="",
            model="gemma2-9b-it",
            timeout_seconds=4,
            fallback_enabled=False,
        )

        with self.assertRaises(RuntimeError):
            service.generate(RISK_RESULT)

    def test_llm_explanation_uses_groq_when_configured(self) -> None:
        service = LLMExplanationService(
            enabled=True,
            api_key="key",
            model="gemma2-9b-it",
            timeout_seconds=4,
            fallback_enabled=True,
        )

        with patch.dict("sys.modules", {"groq": type("FakeGroqModule", (), {"Groq": FakeGroq})}):
            result = service.generate(RISK_RESULT)

        self.assertTrue(result["available"])
        self.assertEqual(result["source"], "groq")
        self.assertEqual(result["explanation"], "High risk because credential collection and URL signals align.")
        self.assertEqual(result["recommendation"], "Do not enter credentials.")


if __name__ == "__main__":
    unittest.main()
