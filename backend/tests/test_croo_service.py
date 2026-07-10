import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
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
        client = TestClient(app)
        response = client.post(
            "/api/audit",
            json={
                "url": "https://example.com/login",
                "title": "Example Login",
                "page_text": "Please verify your account",
                "html": "<html><body><form></form></body></html>",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], "https://example.com/login")
        self.assertIn(data["risk_level"], {"Safe", "Medium", "High"})
        self.assertGreaterEqual(data["risk_score"], 0)

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

            async def connect_websocket(self) -> FakeEventStream:
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


if __name__ == "__main__":
    unittest.main()
