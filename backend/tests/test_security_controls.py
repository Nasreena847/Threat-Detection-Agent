import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import audit as audit_module
from app.api.audit import audit
from app.schemas.request import AuditRequest
from app.services.url_analyzer import validate_public_audit_url


class SecurityControlTests(unittest.TestCase):
    def test_public_audit_url_rejects_local_and_metadata_targets(self) -> None:
        blocked_urls = [
            "http://localhost:8000/admin",
            "http://127.0.0.1:8000/admin",
            "http://10.0.0.5/internal",
            "http://172.16.0.1/internal",
            "http://192.168.1.1/router",
            "http://169.254.169.254/latest/meta-data",
            "http://metadata.google.internal/computeMetadata/v1",
        ]

        for url in blocked_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_public_audit_url(url)

    def test_public_audit_url_allows_public_https_url(self) -> None:
        validate_public_audit_url("https://example.com/login")

    def test_audit_route_returns_bad_request_for_blocked_url(self) -> None:
        with self.assertRaises(HTTPException) as context:
            audit(AuditRequest(url="http://169.254.169.254/latest/meta-data"))

        self.assertEqual(context.exception.status_code, 400)

    def test_audit_api_key_is_required_when_configured(self) -> None:
        with patch.object(audit_module, "settings", SimpleNamespace(audit_api_key="secret", audit_rate_limit_per_minute=60)):
            with self.assertRaises(HTTPException) as context:
                audit(AuditRequest(url="https://example.com"))

        self.assertEqual(context.exception.status_code, 401)

    def test_audit_api_key_allows_matching_header(self) -> None:
        with patch.object(audit_module, "settings", SimpleNamespace(audit_api_key="secret", audit_rate_limit_per_minute=60)):
            response = audit(AuditRequest(url="https://example.com"), x_trusttab_api_key="secret")

        self.assertEqual(response.url, "https://example.com")


if __name__ == "__main__":
    unittest.main()
