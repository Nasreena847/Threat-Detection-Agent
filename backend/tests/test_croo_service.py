import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.audit import audit
from app.schemas.request import AuditRequest
from app.services.audit_pipeline import run_audit_pipeline
from app.services.croo_provider import CrooProvider
from app.services.croo_service import CrooService


class CrooServiceTests(unittest.TestCase):
    def test_invoke_agent_returns_analysis_payload(self) -> None:
        service = CrooService()

        result = service.invoke_agent(
            "threat-detection-agent",
            {
                "url": "https://example.com",
                "title": "Example",
            },
        )

        self.assertEqual(result["agent_id"], "threat-detection-agent")
        self.assertEqual(result["status"], "completed")
        self.assertIn("analysis", result)
        self.assertEqual(result["analysis"]["url"], "https://example.com")

    def test_audit_endpoint_returns_risk_assessment(self) -> None:
        result = audit(
            AuditRequest(
                url="https://example.com/login",
                title="Example Login",
                page_text="Please verify your account",
                html="<html><body><form></form></body></html>",
                forms=1,
                password_fields=1,
                scripts=8,
                iframes=0,
            )
        )

        data = result.model_dump()
        self.assertEqual(data["url"], "https://example.com/login")
        self.assertIn(data["risk_level"], {"Safe", "Medium", "High"})
        self.assertGreaterEqual(data["risk_score"], 30)

    def test_pipeline_separates_trusted_and_phishing_like_pages(self) -> None:
        trusted = run_audit_pipeline(
            url="https://github.com/openai",
            title="GitHub",
            page_text="Open source repository hosting.",
            forms=0,
            scripts=12,
            password_fields=0,
            iframes=0,
        )
        suspicious = run_audit_pipeline(
            url="http://paypal-secure-login.xyz/verify/account?session=abc123&next=wallet",
            title="PayPal Security Alert",
            page_text="Urgent: verify your account password immediately to restore access.",
            forms=2,
            scripts=24,
            password_fields=2,
            iframes=4,
        )

        self.assertLessEqual(trusted["risk_score"], 10)
        self.assertEqual(trusted["risk_level"], "Safe")
        self.assertGreaterEqual(suspicious["risk_score"], 70)
        self.assertEqual(suspicious["risk_level"], "High")

    def test_provider_start_uses_environment_and_event_stream(self) -> None:
        class FakeEventStream:
            def __init__(self, sdk_key: str, ws_url: str) -> None:
                self.sdk_key = sdk_key
                self.ws_url = ws_url
                self.connected = False
                self.handlers = []

            def on_any(self, handler) -> None:
                self.handlers.append(handler)

            async def connect(self) -> None:
                self.connected = True

            async def close(self) -> None:
                self.connected = False

        class FakeAgentClient:
            def __init__(self, config: SimpleNamespace, sdk_key: str) -> None:
                self.config = config
                self.sdk_key = sdk_key
                self.stream = None

            async def connect_websocket(self, service_id: str | None = None) -> FakeEventStream:
                self.service_id = service_id
                self.stream = FakeEventStream(self.sdk_key, self.config.ws_url)
                await self.stream.connect()
                return self.stream

            def close(self) -> None:
                return None

        with patch.dict(
            os.environ,
            {
                "CROO_API_KEY": "demo-key",
                "CROO_BASE_URL": "https://demo.example",
                "CROO_WS_URL": "wss://demo.example/ws",
                "CROO_SERVICE_ID": "service-123",
            },
            clear=False,
        ):
            with patch("app.services.croo_provider.Config", side_effect=lambda base_url, ws_url: SimpleNamespace(base_url=base_url, ws_url=ws_url)), patch(
                "app.services.croo_provider.AgentClient", FakeAgentClient
            ), patch("app.services.croo_provider.EventStream", FakeEventStream):
                provider = CrooProvider()
                asyncio.run(provider.start())

                self.assertTrue(provider._started)
                self.assertIsNotNone(provider._event_stream)
                self.assertTrue(provider._event_stream.connected)
                self.assertEqual(provider._event_stream.sdk_key, "demo-key")
                self.assertIs(provider._agent_client.stream, provider._event_stream)
                self.assertEqual(provider._agent_client.service_id, "service-123")

    def test_provider_accepts_negotiation_event_without_delivery(self) -> None:
        class FakeAgentClient:
            def __init__(self) -> None:
                self.accepted_negotiations: list[str] = []
                self.delivered_orders: list[str] = []

            async def accept_negotiation(self, negotiation_id: str) -> SimpleNamespace:
                self.accepted_negotiations.append(negotiation_id)
                return SimpleNamespace(order=SimpleNamespace(order_id="order-1"))

            async def deliver_order(self, order_id: str, request) -> None:
                self.delivered_orders.append(order_id)

        provider = CrooProvider()
        provider._started = True
        provider._agent_client = FakeAgentClient()

        asyncio.run(provider._handle_event({"negotiation_id": "negotiation-1"}))

        self.assertEqual(provider._agent_client.accepted_negotiations, ["negotiation-1"])
        self.assertEqual(provider._agent_client.delivered_orders, [])


if __name__ == "__main__":
    unittest.main()
