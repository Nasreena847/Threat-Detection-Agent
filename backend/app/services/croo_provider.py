import asyncio
import json
import logging
import os
from typing import Any

from croo import AgentClient, Config, EventStream
from croo.types import DeliverOrderRequest, NegotiateOrderRequest

from app.services.audit_pipeline import run_audit_pipeline

logger = logging.getLogger(__name__)


class CrooProvider:
    """Real CROO integration boundary using the installed SDK."""

    def __init__(self) -> None:
        self._api_key = os.getenv("CROO_API_KEY", "").strip()
        self._base_url = os.getenv("CROO_BASE_URL", "").strip()
        self._ws_url = os.getenv("CROO_WS_URL", "").strip()
        self._agent_client: AgentClient | None = None
        self._event_stream: EventStream | None = None
        self._started = False

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and self._base_url and self._ws_url)

    async def start(self) -> None:
        if self._started:
            logger.info("CROO Provider already started, skipping")
            return
        print("API KEY:", bool(self._api_key))
        print("BASE URL:", self._base_url)
        print("WS URL:", self._ws_url)
        print("IS CONFIGURED:", self.is_configured)
        if not self.is_configured:
            logger.warning("CROO SDK not fully configured; skipping provider startup")
            return

        logger.info("Starting CROO Provider...")
        logger.info("Connecting to CROO EventStream...")
        config = Config(base_url=self._base_url, ws_url=self._ws_url)
        self._agent_client = AgentClient(config, self._api_key)
        self._event_stream = EventStream(self._api_key, self._ws_url)
        self._event_stream.on_any(self._dispatch_event)
        await self._event_stream.connect()
        self._started = True
        logger.info("Connected to CROO EventStream")
        logger.info("Listening for events...")

    async def stop(self) -> None:
        if self._event_stream is not None:
            try:
                await self._event_stream.close()
            except Exception:  # pragma: no cover - defensive path
                logger.exception("Failed to close CROO event stream")
            self._event_stream = None
        if self._agent_client is not None:
            try:
                self._agent_client.close()
            except Exception:  # pragma: no cover - defensive path
                logger.exception("Failed to close CROO agent client")
            self._agent_client = None
        self._started = False

    def _dispatch_event(self, event: Any) -> None:
        if not self._started:
            return
        asyncio.create_task(self._handle_event(event))

    async def _handle_event(self, event: Any) -> None:
        try:
            payload = self._extract_payload(event)
            if not payload:
                return
            await self._deliver_analysis(payload, event)
        except Exception as exc:  # pragma: no cover - runtime path
            logger.exception("CROO event processing failed: %s", exc)

    def invoke_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        analysis = self._perform_analysis(payload)
        if not self.is_configured:
            return {
                "agent_id": agent_id,
                "status": "completed",
                "analysis": analysis,
            }

        try:
            return asyncio.run(self._invoke_agent_async(agent_id, payload, analysis))
        except RuntimeError as exc:
            if "cannot be called from a running event loop" in str(exc):
                logger.warning("Falling back to local analysis because CROO was invoked from an active event loop")
                return {
                    "agent_id": agent_id,
                    "status": "completed",
                    "analysis": analysis,
                }
            raise

    async def _invoke_agent_async(self, agent_id: str, payload: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        await self.start()
        try:
            negotiation = await self._agent_client.negotiate_order(
                NegotiateOrderRequest(
                    service_id=agent_id or "threat-detection-agent",
                    requirements="Analyze a website for phishing and trust risk.",
                    metadata=json.dumps(payload),
                )
            )
            accept_result = await self._agent_client.accept_negotiation(negotiation.negotiation_id)
            delivery = await self._agent_client.deliver_order(
                accept_result.order.order_id,
                DeliverOrderRequest(
                    deliverable_type="analysis",
                    deliverable_schema="application/json",
                    deliverable_text=json.dumps(analysis),
                ),
            )
            return {
                "agent_id": agent_id,
                "status": "delivered",
                "order_id": accept_result.order.order_id,
                "delivery_id": delivery.delivery.delivery_id,
                "analysis": analysis,
            }
        except Exception as exc:
            logger.exception("CROO SDK invocation failed for agent=%s", agent_id)
            raise RuntimeError(f"CROO SDK invocation failed: {exc}") from exc

    async def _deliver_analysis(self, payload: dict[str, Any], event: Any) -> None:
        analysis = self._perform_analysis(payload)
        if not self._agent_client:
            raise RuntimeError("CROO agent client is not initialized")

        order_id = self._extract_order_id(payload, event)
        negotiation_id = self._extract_negotiation_id(payload, event)
        if negotiation_id:
            accept_result = await self._agent_client.accept_negotiation(negotiation_id)
            order_id = accept_result.order.order_id or order_id
        if not order_id:
            raise RuntimeError("No CROO order or negotiation id was provided for delivery")

        await self._agent_client.deliver_order(
            order_id,
            DeliverOrderRequest(
                deliverable_type="analysis",
                deliverable_schema="application/json",
                deliverable_text=json.dumps(analysis),
            ),
        )
        logger.info("Delivered CROO analysis for order=%s", order_id)

    def _perform_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._extract_url(payload)
        if not url:
            raise ValueError("No URL was supplied for CROO analysis")

        title = str(payload.get("title") or payload.get("page_title") or "")
        page_text = str(payload.get("page_text") or payload.get("pageText") or "")
        html = str(payload.get("html") or payload.get("page_html") or "")

        return run_audit_pipeline(url=url, title=title, page_text=page_text, html=html)

    def _extract_payload(self, event: Any) -> dict[str, Any]:
        if isinstance(event, dict):
            raw = event
        else:
            raw = getattr(event, "raw", None)
        if isinstance(raw, dict):
            payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else raw
            if not isinstance(payload, dict):
                return {}
            return payload
        return {}

    def _extract_url(self, payload: dict[str, Any]) -> str:
        for key in ("url", "target_url", "targetUrl", "website_url", "websiteUrl"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested = payload.get("data")
        if isinstance(nested, dict):
            return self._extract_url(nested)
        return ""

    def _extract_order_id(self, payload: dict[str, Any], event: Any) -> str:
        for key in ("order_id", "orderId"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if event is not None:
            value = getattr(event, "order_id", "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _extract_negotiation_id(self, payload: dict[str, Any], event: Any) -> str:
        for key in ("negotiation_id", "negotiationId"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if event is not None:
            value = getattr(event, "negotiation_id", "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
