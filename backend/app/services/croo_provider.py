import asyncio
import inspect
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

try:
    from croo import AgentClient, Config, EventStream
    from croo.types import DeliverableType, DeliverOrderRequest, NegotiateOrderRequest
except ModuleNotFoundError:  # Allows local tests/backend use without the CROO SDK installed.
    class _MissingCrooSDK:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("CROO SDK is not installed. Install the croo package to enable network delivery.")

    AgentClient = _MissingCrooSDK
    Config = _MissingCrooSDK
    EventStream = _MissingCrooSDK

    class DeliverableType:
        TEXT = "text"
        SCHEMA = "schema"

    @dataclass(frozen=True)
    class NegotiateOrderRequest:
        service_id: str
        requirements: str
        metadata: str

    @dataclass(frozen=True)
    class DeliverOrderRequest:
        deliverable_type: str
        deliverable_schema: str
        deliverable_text: str

from app.services.audit_pipeline import run_audit_pipeline

logger = logging.getLogger(__name__)


class CrooProvider:
    """Real CROO integration boundary using the installed SDK."""

    def __init__(self) -> None:
        self._api_key = os.getenv("CROO_API_KEY", "").strip()
        self._base_url = os.getenv("CROO_BASE_URL", "").strip()
        self._ws_url = os.getenv("CROO_WS_URL", "").strip()
        self._service_id = os.getenv("CROO_SERVICE_ID", "").strip()
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
        if not self.is_configured:
            logger.warning("CROO SDK not fully configured; skipping provider startup")
            return

        logger.info("Starting CROO Provider...")
        logger.info(
            "CROO provider configured for base_url=%s ws_url=%s service_id=%s",
            self._base_url,
            self._ws_url,
            self._service_id or "not set",
        )
        logger.info("Connecting to CROO EventStream...")
        config = Config(base_url=self._base_url, ws_url=self._ws_url)
        self._agent_client = AgentClient(config, self._api_key)
        if hasattr(self._agent_client, "connect_websocket"):
            self._event_stream = await self._connect_websocket()
        else:
            self._event_stream = EventStream(self._api_key, self._ws_url)
            await self._event_stream.connect()
        self._event_stream.on_any(self._dispatch_event)
        self._started = True
        logger.info("Connected to CROO EventStream")
        logger.info("Listening for events...")

    async def _connect_websocket(self):
        connect_websocket = self._agent_client.connect_websocket
        signature = inspect.signature(connect_websocket)

        if self._service_id:
            for parameter_name in ("service_id", "serviceId", "service"):
                if parameter_name in signature.parameters:
                    logger.info("Connecting CROO websocket with %s=%s", parameter_name, self._service_id)
                    return await connect_websocket(**{parameter_name: self._service_id})
            logger.info("CROO SDK connect_websocket does not accept service_id; connecting without it")

        return await connect_websocket()

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
            negotiation_id = self._extract_negotiation_id(payload, event)
            order_id = self._extract_order_id(payload, event)

            if negotiation_id and not order_id:
                await self._accept_negotiation(negotiation_id)
                return

            if not payload:
                logger.info("Ignoring CROO event without payload: %r", event)
                return
            await self._deliver_analysis(payload, event)
        except Exception as exc:  # pragma: no cover - runtime path
            logger.exception("CROO event processing failed: %s", exc)

    async def _accept_negotiation(self, negotiation_id: str) -> None:
        if not self._agent_client:
            raise RuntimeError("CROO agent client is not initialized")

        await self._agent_client.accept_negotiation(negotiation_id)
        logger.info("Accepted CROO negotiation=%s", negotiation_id)

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
        service_id = agent_id.strip()
        if not service_id:
            raise ValueError("A real CROO service id must be provided; refusing to use a hardcoded fallback.")

        await self.start()
        try:
            negotiation = await self._agent_client.negotiate_order(
                NegotiateOrderRequest(
                    service_id=service_id,
                    requirements="Analyze a website for phishing and trust risk.",
                    metadata=json.dumps(payload),
                )
            )
            accept_result = await self._agent_client.accept_negotiation(negotiation.negotiation_id)
            delivery = await self._agent_client.deliver_order(
                accept_result.order.order_id,
                DeliverOrderRequest(
                    deliverable_type=DeliverableType.SCHEMA,
                    deliverable_schema=json.dumps(analysis),
                    deliverable_text="",
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
                deliverable_type=DeliverableType.SCHEMA,
                deliverable_schema=json.dumps(analysis),
                deliverable_text="",
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
        forms = self._extract_int(payload, "forms", "form_count", "formCount")
        scripts = self._extract_int(payload, "scripts", "script_count", "scriptCount")
        password_fields = self._extract_int(payload, "password_fields", "passwordFields", "password_count", "passwordCount")
        iframes = self._extract_int(payload, "iframes", "iframe_count", "iframeCount")

        return run_audit_pipeline(
            url=url,
            title=title,
            page_text=page_text,
            html=html,
            forms=forms,
            scripts=scripts,
            password_fields=password_fields,
            iframes=iframes,
        )

    def _extract_payload(self, event: Any) -> dict[str, Any]:
        if isinstance(event, dict):
            raw = event
        else:
            raw = (
                getattr(event, "payload", None)
                or getattr(event, "data", None)
                or getattr(event, "raw", None)
            )
        if isinstance(raw, dict):
            for key in ("payload", "data", "body"):
                if isinstance(raw.get(key), dict):
                    payload = raw[key]
                    break
            else:
                payload = raw
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

    def _extract_int(self, payload: dict[str, Any], *keys: str) -> int | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                return max(0, value)
            if isinstance(value, str) and value.strip().isdigit():
                return max(0, int(value.strip()))
        return None

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
        for key in ("negotiation_id", "negotiationId", "id"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if event is not None:
            for key in ("negotiation_id", "negotiationId", "id"):
                value = getattr(event, key, "")
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        provider = CrooProvider()
        print("is_configured:", provider.is_configured)
        await provider.start()
        print("started:", provider._started)
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await provider.stop()

    asyncio.run(_main())
