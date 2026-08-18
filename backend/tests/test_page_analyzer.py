import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.page_analyzer import analyze_page
from app.services.risk_engine import calculate_risk


class PageAnalyzerTests(unittest.TestCase):
    def test_ad_density_adds_warning_signal(self) -> None:
        baseline = analyze_page(
            url="https://example.com/article",
            title="Example Article",
            page_text="A regular article with useful content.",
            html="<html><body><article>Useful content</article></body></html>",
        )
        ad_heavy = analyze_page(
            url="https://example.com/article",
            title="Example Article",
            page_text="A regular article with useful content.",
            html="<html><body><article>Useful content</article></body></html>",
            ads=18,
        )

        self.assertGreater(ad_heavy["score"], baseline["score"])
        self.assertGreaterEqual(ad_heavy["score"], 50)
        self.assertTrue(any("Too many ads detected" in reason for reason in ad_heavy["reasons"]))
        self.assertTrue(any("scam, malware, or virus-like redirects" in reason for reason in ad_heavy["reasons"]))
        self.assertEqual(ad_heavy["ad_risk"]["severity"], "critical")

    def test_ad_risk_affects_final_risk_meter_score(self) -> None:
        page = analyze_page(
            url="https://trusted.example/article",
            title="Trusted Article",
            page_text="Normal article content.",
            html="<html><body><article>Normal article content.</article></body></html>",
            ads=8,
        )
        result = calculate_risk(
            {"score": 0, "reasons": []},
            page,
            {"score": 0, "reasons": ["Domain reputation appears trusted for trusted.example."]},
            {"score": 0, "reasons": [], "available": False},
        )

        self.assertGreaterEqual(result["risk_score"], 58)
        self.assertEqual(result["components"]["ads"], page["ad_risk"]["score"])
        self.assertEqual(result["ad_risk"]["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
