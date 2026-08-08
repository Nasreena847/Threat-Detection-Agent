import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ml_classifier import MLClassifierService, extract_url_only_features
from app.services.risk_engine import calculate_risk


class FakeRandomForest:
    classes_ = [0, 1]

    def __init__(self, probability: float) -> None:
        self.probability = probability

    def predict_proba(self, _model_input):
        return [[1 - self.probability, self.probability]]


class MLClassifierTests(unittest.TestCase):
    def test_extract_url_only_features_matches_training_columns(self) -> None:
        features = extract_url_only_features("http://paypal-secure-login.xyz/verify/account?token=abc123&next=wallet")

        self.assertEqual(features["qty_dot_url"], 1)
        self.assertEqual(features["qty_hyphen_domain"], 2)
        self.assertEqual(features["qty_questionmark_url"], 1)
        self.assertEqual(features["qty_params"], 2)
        self.assertEqual(features["domain_in_ip"], 0)
        self.assertGreater(features["length_url"], 0)

    def test_ml_classifier_uses_predict_proba(self) -> None:
        service = MLClassifierService(
            model_path="missing.joblib",
            manifest_path="model/feature_manifest.json",
            enabled=True,
            phishing_threshold=0.5,
            model=FakeRandomForest(0.87),
            feature_names=["length_url", "qty_dot_url", "qty_params"],
        )

        result = service.analyze("https://example.com/login?next=account")

        self.assertTrue(result["available"])
        self.assertEqual(result["score"], 87)
        self.assertEqual(result["verdict"], "phishing-like")
        self.assertEqual(result["feature_count"], 3)

    def test_ml_classifier_missing_model_is_non_fatal(self) -> None:
        service = MLClassifierService(
            model_path="missing.joblib",
            manifest_path="missing.json",
            enabled=True,
            phishing_threshold=0.5,
        )

        result = service.analyze("https://example.com")

        self.assertFalse(result["available"])
        self.assertEqual(result["score"], 0)

    def test_risk_engine_does_not_let_ml_alone_force_high_risk(self) -> None:
        result = calculate_risk(
            {"score": 0, "reasons": []},
            {"score": 0, "reasons": []},
            {"score": 0, "reasons": []},
            {"score": 90, "reasons": ["ML signal"], "available": True},
        )

        self.assertLessEqual(result["risk_score"], 25)
        self.assertEqual(result["components"]["ml"], 90)
        self.assertIn("not raised", " ".join(result["reasons"]))

    def test_risk_engine_uses_high_ml_score_when_rule_signals_corroborate_it(self) -> None:
        result = calculate_risk(
            {"score": 35, "reasons": ["Suspicious URL"]},
            {"score": 30, "reasons": ["Suspicious page"]},
            {"score": 8, "reasons": []},
            {"score": 90, "reasons": ["ML signal"], "available": True},
        )

        self.assertGreaterEqual(result["risk_score"], 70)
        self.assertEqual(result["components"]["ml"], 90)
        self.assertIn("ML signal", result["reasons"])

    def test_risk_engine_caps_clean_trusted_domain_even_with_high_ml_score(self) -> None:
        result = calculate_risk(
            {"score": 0, "reasons": []},
            {"score": 0, "reasons": []},
            {"score": 0, "reasons": ["Domain reputation appears trusted for github.com."]},
            {"score": 95, "reasons": ["ML signal"], "available": True},
        )

        self.assertLessEqual(result["risk_score"], 25)
        self.assertEqual(result["risk_level"], "Safe")


if __name__ == "__main__":
    unittest.main()
