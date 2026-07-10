import logging
from typing import Any

from app.services.croo_provider import CrooProvider

logger = logging.getLogger(__name__)


class CrooService:
    """Isolated CROO integration boundary with SDK-backed analysis delivery."""

    def __init__(self) -> None:
        self._provider = CrooProvider()

    def discover_agents(self) -> list[dict[str, object]]:
        if not self._provider.is_configured:
            return [
                {
                    "id": "threat-detection-agent",
                    "name": "Threat Detection Agent",
                    "description": "Local risk analysis agent backed by the existing audit pipeline.",
                    "available": False,
                }
            ]
        return [
            {
                "id": "threat-detection-agent",
                "name": "Threat Detection Agent",
                "description": "Uses the CROO SDK to deliver website risk analysis results.",
                "available": True,
            }
        ]

    def invoke_agent(self, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        try:
            result = self._provider.invoke_agent(agent_id, self._normalize_payload(payload))
            return self._wrap_result(result)
        except Exception as exc:  # pragma: no cover - runtime path
            logger.exception("CROO service invocation failed for agent=%s", agent_id)
            return {
                "agent_id": agent_id,
                "status": "failed",
                "error": str(exc),
                "analysis": self._fallback_analysis(payload),
            }

    async def start(self) -> None:
        logger.info("CROO Service startup initiated")
        await self._provider.start()
        logger.info("CROO Service startup complete")

    async def stop(self) -> None:
        logger.info("CROO Service shutdown initiated")
        await self._provider.stop()
        logger.info("CROO Service shutdown complete")

    def _normalize_payload(self, payload: dict[str, object]) -> dict[str, Any]:
        if not payload:
            return {}
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                normalized[key] = value
            elif isinstance(value, (list, dict)):
                normalized[key] = value
            else:
                normalized[key] = str(value)
        return normalized

    def _wrap_result(self, result: Any) -> dict[str, object]:
        if isinstance(result, dict):
            return result
        return {"status": "completed", "result": result}

    def _fallback_analysis(self, payload: dict[str, object]) -> dict[str, object]:
        url = str(payload.get("url") or payload.get("target_url") or "")
        return {
            "url": url,
            "risk_score": 0,
            "risk_level": "Safe",
            "reasons": ["CROO delivery failed; local analysis is unavailable."],
            "recommendation": "Verify the CROO SDK configuration before retrying.",
            "explanation": "The CROO service could not deliver a result.",
        }


croo_service = CrooService()
