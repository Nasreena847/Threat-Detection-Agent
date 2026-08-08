import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import audit as audit_module
from app.api.audit import audit
from app.schemas.request import AuditRequest
from app.services.scan_history import ScanHistoryStore


class ScanHistoryStoreTests(unittest.TestCase):
    def test_store_saves_lists_gets_and_clears_scans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ScanHistoryStore(
                db_path=str(Path(temp_dir) / "scan_history.sqlite3"),
                enabled=True,
                retention_limit=10,
            )

            scan_id = store.save(
                {
                    "url": "https://example.com/login",
                    "risk_score": 42,
                    "risk_level": "Medium",
                    "explanation_source": {"source": "deterministic"},
                    "reasons": ["Login form detected."],
                }
            )

            self.assertIsInstance(scan_id, int)
            scans = store.list_recent()
            self.assertEqual(len(scans), 1)
            self.assertEqual(scans[0]["domain"], "example.com")
            self.assertEqual(scans[0]["risk_score"], 42)
            self.assertEqual(scans[0]["explanation_source"], "deterministic")

            stored = store.get(scan_id or 0)
            self.assertIsNotNone(stored)
            self.assertEqual(stored["report"]["url"], "https://example.com/login")

            self.assertEqual(store.clear(), 1)
            self.assertEqual(store.list_recent(), [])

    def test_store_prunes_old_scans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ScanHistoryStore(
                db_path=str(Path(temp_dir) / "scan_history.sqlite3"),
                enabled=True,
                retention_limit=2,
            )

            for index in range(3):
                store.save(
                    {
                        "url": f"https://example.com/{index}",
                        "risk_score": index,
                        "risk_level": "Safe",
                    }
                )

            scans = store.list_recent(limit=10)
            self.assertEqual(len(scans), 2)
            self.assertEqual([scan["url"] for scan in scans], ["https://example.com/2", "https://example.com/1"])

    def test_disabled_store_noops(self) -> None:
        store = ScanHistoryStore(db_path="unused.sqlite3", enabled=False, retention_limit=10)

        self.assertIsNone(store.save({"url": "https://example.com"}))
        self.assertEqual(store.list_recent(), [])
        self.assertIsNone(store.get(1))
        self.assertEqual(store.clear(), 0)


class AuditScanHistoryTests(unittest.TestCase):
    def test_audit_response_includes_scan_id_from_history_store(self) -> None:
        class FakeHistoryStore:
            def save(self, report: dict[str, object]) -> int:
                self.report = report
                return 123

        fake_store = FakeHistoryStore()
        with patch.object(audit_module, "scan_history_store", fake_store):
            response = audit(AuditRequest(url="https://example.com"))

        self.assertEqual(response.scan_id, 123)
        self.assertEqual(fake_store.report["url"], "https://example.com")


if __name__ == "__main__":
    unittest.main()
