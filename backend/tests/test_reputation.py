import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.reputation import DNSReputationClient, ReputationService, VirusTotalClient, _virustotal_url_id


class FakeVirusTotalClient:
    def __init__(self, result: dict[str, object] | None) -> None:
        self.result = result

    def analyze_url(self, url: str) -> dict[str, object] | None:
        return self.result


class FakeDNSClient:
    def __init__(self, result: dict[str, object] | None) -> None:
        self.result = result

    def analyze_url(self, url: str) -> dict[str, object] | None:
        return self.result


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, object]:
        return self._payload


class ReputationTests(unittest.TestCase):
    def test_virustotal_url_id_uses_unpadded_urlsafe_base64(self) -> None:
        self.assertEqual(_virustotal_url_id("https://example.com"), "aHR0cHM6Ly9leGFtcGxlLmNvbQ")

    def test_reputation_uses_local_result_without_virustotal(self) -> None:
        service = ReputationService(FakeVirusTotalClient(None), FakeDNSClient(None))

        result = service.analyze("https://github.com/openai")

        self.assertEqual(result["provider"], "local")
        self.assertEqual(result["score"], 0)

    def test_reputation_merges_virustotal_detections(self) -> None:
        service = ReputationService(
            FakeVirusTotalClient(
                {
                    "score": 70,
                    "reasons": ["VirusTotal threat intelligence reported 3 malicious and 1 suspicious vendor detections."],
                    "provider": "virustotal",
                    "available": True,
                    "stats": {"malicious": 3, "suspicious": 1, "harmless": 20, "undetected": 10},
                    "reputation": -5,
                }
            ),
            FakeDNSClient(None),
        )

        result = service.analyze("https://unknown-example.test/login")

        self.assertEqual(result["provider"], "local+virustotal")
        self.assertGreaterEqual(result["score"], 70)
        self.assertIn("virustotal", result)
        self.assertIn("VirusTotal", " ".join(result["reasons"]))

    def test_reputation_merges_dns_anomalies(self) -> None:
        service = ReputationService(
            FakeVirusTotalClient(None),
            FakeDNSClient(
                {
                    "score": 35,
                    "reasons": ["DNS check resolved the hostname to private, local, or reserved address space."],
                    "provider": "dns",
                    "available": True,
                    "records": {"a": ["10.0.0.10"], "aaaa": [], "mx": [], "ns": ["ns1.example.test"], "txt": []},
                }
            ),
        )

        result = service.analyze("https://unknown-example.test/login")

        self.assertEqual(result["provider"], "local+dns")
        self.assertGreaterEqual(result["score"], 35)
        self.assertIn("dns", result)
        self.assertIn("DNS check", " ".join(result["reasons"]))

    def test_virustotal_client_caches_reports(self) -> None:
        response = FakeResponse(
            200,
            {
                "data": {
                    "attributes": {
                        "last_analysis_stats": {
                            "malicious": 1,
                            "suspicious": 0,
                            "harmless": 20,
                            "undetected": 5,
                        },
                        "reputation": -1,
                    },
                    "links": {"self": "https://www.virustotal.com/api/v3/urls/id"},
                }
            },
        )
        client = VirusTotalClient("vt-key", timeout_seconds=3, cache_ttl_seconds=60, submit_unknown_urls=False)

        with patch("app.services.reputation.httpx.get", return_value=response) as get_mock:
            first = client.analyze_url("https://example.com")
            second = client.analyze_url("https://example.com")

        self.assertEqual(get_mock.call_count, 1)
        self.assertEqual(first["cache"], "miss")
        self.assertEqual(second["cache"], "hit")
        self.assertGreater(first["score"], 0)

    def test_virustotal_client_can_submit_unknown_url_when_enabled(self) -> None:
        client = VirusTotalClient("vt-key", timeout_seconds=3, cache_ttl_seconds=0, submit_unknown_urls=True)
        post_response = FakeResponse(
            200,
            {"data": {"id": "analysis-123", "type": "analysis"}},
        )

        with patch("app.services.reputation.httpx.get", return_value=FakeResponse(404, {})), patch(
            "app.services.reputation.httpx.post", return_value=post_response
        ) as post_mock:
            result = client.analyze_url("https://new-example.test")

        self.assertEqual(post_mock.call_count, 1)
        self.assertTrue(result["submitted"])
        self.assertEqual(result["analysis_id"], "analysis-123")

    def test_dns_client_returns_unavailable_without_resolver_dependency(self) -> None:
        client = DNSReputationClient(enabled=True, timeout_seconds=1)

        with patch("app.services.reputation.dns", None):
            result = client.analyze_url("https://example.com")

        self.assertEqual(result["provider"], "dns")
        self.assertFalse(result["available"])


if __name__ == "__main__":
    unittest.main()
