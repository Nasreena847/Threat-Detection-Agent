import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.page_analyzer import analyze_page


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
        self.assertTrue(any("advertising density" in reason for reason in ad_heavy["reasons"]))


if __name__ == "__main__":
    unittest.main()
