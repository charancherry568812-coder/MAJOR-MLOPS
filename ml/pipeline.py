"""ML preprocessing, model training, evaluation, and explainability.

This single module contains the complete ML pipeline to avoid deep import chains.
"""

from __future__ import annotations

import json
import os
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════
# PREPROCESSING
# ══════════════════════════════════════════════════════════════

USE_CASE_FEATURES = {
    "credit_risk": {
        "features": [
            "age", "income", "employment_years", "credit_score", "loan_amount",
            "loan_term", "existing_loans", "debt_to_income", "account_balance",
            "late_payments", "transaction_count",
        ],
        "target": "target_default",
    },
    "fraud": {
        "features": [
            "amount_deviation", "velocity_score", "num_devices",
            "account_age_months", "merchant_category_diversity",
            "transaction_count", "credit_score", "income",
        ],
        "target": "is_fraud",
    },
    "churn": {
        "features": [
            "account_age_months", "transaction_count", "income", "credit_score",
            "existing_loans", "account_balance", "num_devices", "merchant_category_diversity",
        ],
        "target": "churn_label",
    },
    "transaction_risk": {
        "features": [
            "transaction_amount", "amount_deviation", "velocity_score",
            "credit_score", "account_age_months", "transaction_count",
        ],
        "target": "transaction_risk_label",
    },
    "aml": {
        "features": [
            "transaction_amount", "velocity_score", "amount_deviation",
            "num_devices", "merchant_category_diversity", "account_age_months",
        ],
        "target": "aml_flag",
    },
}


class Preprocessor:
    """Reusable preprocessing pipeline for all banking use cases."""

    def __init__(self, use_case: str = "credit_risk"):
        self.use_case = use_case
        config = USE_CASE_FEATURES.get(use_case, USE_CASE_FEATURES["credit_risk"])
        self.feature_names: List[str] = list(config["features"])
        self.target_col: str = config["target"]
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="median")
        self._fitted = False

    def _prepare_target(self, df: pd.DataFrame) -> pd.Series:
        """Extract or derive target column."""
        if self.target_col in df.columns:
            return df[self.target_col]
        if self.target_col == "target_default" and "is_default" in df.columns:
            return df["is_default"]
        if self.target_col == "churn_label" and "churn_probability" in df.columns:
            return (df["churn_probability"] > 0.5).astype(int)
        if self.target_col == "transaction_risk_label" and "transaction_risk_score" in df.columns:
            return (df["transaction_risk_score"] > 0.6).astype(int)
        return pd.Series(np.zeros(len(df)))

    def _align_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map aliases and ensure all expected features exist."""
        aligned = df.copy()
        alias_map = {
            "transaction_frequency": "transaction_count",
            "previous_defaults": "late_payments",
            "default_history": "late_payments",
            "transaction_amount_avg": "transaction_amount",
        }
        for old_col, target_col in alias_map.items():
            if old_col in aligned.columns and target_col not in aligned.columns:
                aligned[target_col] = aligned[old_col]

        for feat in self.feature_names:
            if feat not in aligned.columns:
                # Reverse alias check
                rev = {v: k for k, v in alias_map.items()}.get(feat)
                if rev and rev in aligned.columns:
                    aligned[feat] = aligned[rev]
                else:
                    aligned[feat] = 0.0

        return aligned

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Fit on training split and return normalized numpy partitions."""
        aligned = self._align_dataframe(df)
        X = aligned[self.feature_names].values.astype(float)
        y = self._prepare_target(df).values.astype(int)

        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

        # Fit transformers strictly on training partition
        X_train = self.imputer.fit_transform(X_train)
        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(self.imputer.transform(X_val))
        X_test = self.scaler.transform(self.imputer.transform(X_test))
        self._fitted = True

        return X_train, X_val, X_test, y_train, y_val, y_test

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform new data using fitted scaler and imputer."""
        aligned = self._align_dataframe(df)
        X = aligned[self.feature_names].values.astype(float)
        if self._fitted:
            X = self.imputer.transform(X)
            X = self.scaler.transform(X)
        return X

    def save(self, path: str):
        """Serialize complete preprocessor instance."""
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "Preprocessor":
        """Load serialized preprocessor, with backwards compatibility."""
        obj = joblib.load(path)
        if isinstance(obj, Preprocessor):
            return obj
        p = cls(obj.get("use_case", "credit_risk"))
        p.scaler = obj["scaler"]
        p.imputer = obj["imputer"]
        p.feature_names = obj["feature_names"]
        p.target_col = obj.get("target_col", "target_default")
        p._fitted = obj.get("fitted", True)
        return p


# ══════════════════════════════════════════════════════════════
# ML MODELS
# ══════════════════════════════════════════════════════════════

class BaseMLModel(ABC):
    """Abstract base for all ML models."""

    def __init__(self, use_case: str, algorithm: str):
        self.use_case = use_case
        self.algorithm = algorithm
        self.model = None
        self._feature_names: List[str] = []

    @abstractmethod
    def _create_model(self):
        pass

    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        self.model = self._create_model()
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_val if X_val is not None else X_train)
        y_true = y_val if y_val is not None else y_train
        y_proba = self.model.predict_proba(X_val if X_val is not None else X_train)[:, 1] if hasattr(self.model, "predict_proba") else None
        return evaluate_model(y_true, y_pred, y_proba)

    def predict(self, X) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        return np.column_stack([1 - self.model.predict(X).astype(float), self.model.predict(X).astype(float)])

    def get_params(self) -> dict:
        return self.model.get_params() if self.model else {}

    def save(self, path: str):
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)

    @property
    def feature_importance(self) -> Dict[str, float]:
        if hasattr(self.model, "feature_importances_"):
            return {f: round(float(v), 4) for f, v in zip(self._feature_names, self.model.feature_importances_)}
        if hasattr(self.model, "coef_"):
            return {f: round(float(abs(v)), 4) for f, v in zip(self._feature_names, self.model.coef_[0])}
        return {}


# Concrete implementations
class LRModel(BaseMLModel):
    def _create_model(self):
        return LogisticRegression(C=1.0, max_iter=1000, random_state=42)

class RFModel(BaseMLModel):
    def _create_model(self):
        return RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)

class GBModel(BaseMLModel):
    def _create_model(self):
        return GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)

class XGBModel(BaseMLModel):
    def _create_model(self):
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, use_label_encoder=False,
                                 eval_metric="logloss", random_state=42, n_jobs=-1)
        except ImportError:
            return GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)

class IFModel(BaseMLModel):
    def _create_model(self):
        return IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)

    def train(self, X_train, y_train, X_val=None, y_val=None):
        self.model = self._create_model()
        self.model.fit(X_train)
        y_pred = np.where(self.model.predict(X_val if X_val is not None else X_train) == -1, 1, 0)
        y_true = y_val if y_val is not None else y_train
        return evaluate_model(y_true, y_pred)

    def predict(self, X):
        return np.where(self.model.predict(X) == -1, 1, 0)

    def predict_proba(self, X):
        scores = -self.model.score_samples(X)
        scores = np.clip(scores / scores.max(), 0, 1)
        return np.column_stack([1 - scores, scores])


# ── Model Factory ─────────────────────────────────────────────
MODEL_REGISTRY = {
    ("credit_risk", "logistic_regression"): lambda: LRModel("credit_risk", "logistic_regression"),
    ("credit_risk", "random_forest"): lambda: RFModel("credit_risk", "random_forest"),
    ("credit_risk", "gradient_boosting"): lambda: GBModel("credit_risk", "gradient_boosting"),
    ("credit_risk", "xgboost"): lambda: XGBModel("credit_risk", "xgboost"),
    ("fraud", "random_forest"): lambda: RFModel("fraud", "random_forest"),
    ("fraud", "xgboost"): lambda: XGBModel("fraud", "xgboost"),
    ("fraud", "logistic_regression"): lambda: LRModel("fraud", "logistic_regression"),
    ("fraud", "isolation_forest"): lambda: IFModel("fraud", "isolation_forest"),
    ("churn", "logistic_regression"): lambda: LRModel("churn", "logistic_regression"),
    ("churn", "random_forest"): lambda: RFModel("churn", "random_forest"),
    ("churn", "gradient_boosting"): lambda: GBModel("churn", "gradient_boosting"),
    ("transaction_risk", "random_forest"): lambda: RFModel("transaction_risk", "random_forest"),
    ("transaction_risk", "gradient_boosting"): lambda: GBModel("transaction_risk", "gradient_boosting"),
    ("aml", "isolation_forest"): lambda: IFModel("aml", "isolation_forest"),
    ("aml", "random_forest"): lambda: RFModel("aml", "random_forest"),
}


def create_model(use_case: str, algorithm: str) -> BaseMLModel:
    factory = MODEL_REGISTRY.get((use_case, algorithm))
    if not factory:
        raise ValueError(f"Unknown model: {use_case}/{algorithm}. Available: {list(MODEL_REGISTRY.keys())}")
    return factory()


def get_available_algorithms(use_case: str) -> List[str]:
    return [alg for (uc, alg) in MODEL_REGISTRY if uc == use_case]


def get_all_use_cases() -> List[str]:
    return list(set(uc for uc, _ in MODEL_REGISTRY))


# ══════════════════════════════════════════════════════════════
# EVALUATION
# ══════════════════════════════════════════════════════════════

def evaluate_model(y_true, y_pred, y_proba=None) -> Dict[str, Any]:
    """Calculate classification metrics."""
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }
    if y_proba is not None:
        try:
            metrics["auc"] = round(float(roc_auc_score(y_true, y_proba)), 4)
        except ValueError:
            metrics["auc"] = 0.0
    else:
        metrics["auc"] = 0.0
    return metrics


# ══════════════════════════════════════════════════════════════
# SHAP EXPLAINABILITY
# ══════════════════════════════════════════════════════════════

def explain_prediction(model, X_single: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """Generate SHAP explanation for a single prediction."""
    try:
        import shap
        if hasattr(model, "feature_importances_"):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.LinearExplainer(model, X_single)

        sv = explainer.shap_values(X_single)
        if isinstance(sv, list):
            values = sv[1][0] if len(sv) > 1 else sv[0][0]
        else:
            values = sv[0] if len(sv.shape) > 1 else sv

        explanation = {}
        for i, fn in enumerate(feature_names):
            if i < len(values):
                explanation[fn] = round(float(values[i]), 4)

        sorted_exp = dict(sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True))
        return {
            "shap_values": sorted_exp,
            "top_features": dict(list(sorted_exp.items())[:5]),
        }
    except Exception:
        # Fallback to feature importance
        if hasattr(model, "feature_importances_"):
            fi = model.feature_importances_
            explanation = {fn: round(float(fi[i]), 4) for i, fn in enumerate(feature_names) if i < len(fi)}
            sorted_exp = dict(sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True))
            return {"shap_values": sorted_exp, "top_features": dict(list(sorted_exp.items())[:5])}
        return {"shap_values": {}, "top_features": {}}


# ══════════════════════════════════════════════════════════════
# TRAINING PIPELINE
# ══════════════════════════════════════════════════════════════

def train_model(
    dataset_path: str,
    use_case: str = "credit_risk",
    algorithm: str = "random_forest",
    output_dir: str = "./model_storage",
) -> Dict[str, Any]:
    """Complete training pipeline: preprocess → train → evaluate → save."""
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    df = pd.read_csv(dataset_path)

    # Preprocess
    preprocessor = Preprocessor(use_case)
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.fit_transform(df)

    # Train
    model = create_model(use_case, algorithm)
    model._feature_names = preprocessor.feature_names
    val_metrics = model.train(X_train, y_train, X_val, y_val)

    # Evaluate on test
    y_test_pred = model.predict(X_test)
    y_test_proba = model.predict_proba(X_test)[:, 1] if hasattr(model.model, "predict_proba") else None
    test_metrics = evaluate_model(y_test, y_test_pred, y_test_proba)

    # Feature importance
    fi = model.feature_importance

    # Save
    model_id = f"{use_case}_{algorithm}"
    model_path = os.path.join(output_dir, f"{model_id}_model.joblib")
    preprocessor_path = os.path.join(output_dir, f"{model_id}_preprocessor.joblib")
    model.save(model_path)
    preprocessor.save(preprocessor_path)

    return {
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "feature_importance": fi,
        "feature_names": preprocessor.feature_names,
        "train_size": len(y_train),
        "val_size": len(y_val),
        "test_size": len(y_test),
    }


# ══════════════════════════════════════════════════════════════
# MODEL SERVER (for serving predictions)
# ══════════════════════════════════════════════════════════════

class ModelServer:
    """In-memory model serving with thread-safe loading."""

    def __init__(self):
        self._models: Dict[str, Any] = {}  # version_id -> (model, preprocessor, feature_names)

    def load_model(self, version_id: str, model_path: str, preprocessor_path: Optional[str] = None):
        model = joblib.load(model_path)
        preprocessor = None
        feature_names = []
        if preprocessor_path and os.path.exists(preprocessor_path):
            p_data = joblib.load(preprocessor_path)
            if isinstance(p_data, dict):
                preprocessor = Preprocessor.__new__(Preprocessor)
                preprocessor.scaler = p_data["scaler"]
                preprocessor.imputer = p_data["imputer"]
                preprocessor.feature_names = p_data["feature_names"]
                preprocessor._fitted = p_data["fitted"]
                feature_names = p_data["feature_names"]
            else:
                preprocessor = p_data
                feature_names = getattr(preprocessor, "feature_names", [])
        self._models[version_id] = (model, preprocessor, feature_names)

    def unload_model(self, version_id: str):
        self._models.pop(version_id, None)

    def is_loaded(self, version_id: str) -> bool:
        return version_id in self._models

    def predict(self, version_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        if version_id not in self._models:
            raise ValueError(f"Model {version_id} not loaded")

        model, preprocessor, feature_names = self._models[version_id]
        df = pd.DataFrame([features])

        if preprocessor:
            X = preprocessor.transform(df)
        else:
            X = df.select_dtypes(include="number").values

        proba = model.predict_proba(X)[0] if hasattr(model, "predict_proba") else [0.5, 0.5]
        probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        risk_score = int(probability * 100)

        if probability >= 0.7:
            risk_category = "HIGH_RISK"
        elif probability >= 0.4:
            risk_category = "MEDIUM_RISK"
        else:
            risk_category = "LOW_RISK"

        explanation = explain_prediction(model, X, feature_names or list(features.keys()))

        return {
            "prediction": risk_category,
            "probability": round(probability, 4),
            "risk_score": risk_score,
            "risk_category": risk_category,
            "explanation": explanation.get("top_features", {}),
        }


# Singleton
model_server = ModelServer()
