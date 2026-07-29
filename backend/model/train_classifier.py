import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from pathlib import Path
DATA_PATH = str(Path(__file__).parent / "dataset_small.csv")
TARGET = "phishing"

NETWORK_FEATURES = [
    "time_response", "domain_spf", "asn_ip", "time_domain_activation",
    "time_domain_expiration", "qty_ip_resolved", "qty_nameservers",
    "qty_mx_servers", "ttl_hostname", "tls_ssl_certificate", "qty_redirects",
    "url_google_index", "domain_google_index",
]

def train_and_evaluate(df:pd.DataFrame, feature_cols: list[str], name: str):
    X = df[feature_cols]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42, stratify=y)

    model = RandomForestClassifier(
        n_estimators = 300, 
        max_depth  = None, 
        min_samples_leaf = 2, 
        n_jobs = -1, 
        random_state = 42,
        class_weight = "balanced"
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    print(classification_report(y_test, y_pred, target_names=["legitimate", "phishing"]))
    print("ROC-AUC:", round(roc_auc_score(y_test, y_proba), 4))
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    print(confusion_matrix(y_test, y_pred))

    # top feature importances -- useful for sanity-checking the model isn't
    # keying off something spurious

    importances = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: -x[1])[:10]
    print("\nTop 10 most important features:")
    for feat, imp in importances:
        print(f"  {feat}: {imp:.4f}")

    return model


def main():
    df = pd.read_csv(DATA_PATH)
    all_features = [c for c in df.columns if c != TARGET]
    url_only_features = [c for c in all_features if c not in NETWORK_FEATURES]

    full_model = train_and_evaluate(df, all_features, "FULL MODEL (111 features)")
    url_only_model = train_and_evaluate(df, url_only_features, "URL-ONLY MODEL (98 features, no network calls)")

    joblib.dump(full_model, "full_model.joblib")
    joblib.dump(url_only_model, "url_only_model.joblib")

    with open("feature_manifest.json", "w") as f:
        json.dump({
            "full_model_features": all_features,
            "url_only_model_features": url_only_features,
            "network_dependent_features": NETWORK_FEATURES,
            "target": TARGET,
            "target_meaning": {"0": "legitimate", "1": "phishing"},
        }, f, indent=2)

    print("\nSaved: full_model.joblib, url_only_model.joblib, feature_manifest.json")


if __name__ == "__main__":
    main()
