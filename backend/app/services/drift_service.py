"""Advanced Statistical Data Drift (PSI, KS-Test, Categorical), Model Drift, and Concept Drift Engine."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from app.models.drift_quality import AdvancedDataDriftReport, ModelDriftReport, ConceptDriftReport
from app.models.ml_model import MLModel, ModelVersion


class StatisticalDriftService:
    """Scientific Data Drift & Model Performance Decay Analytics."""

    @staticmethod
    def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
        """Calculate Population Stability Index (PSI) using quantile binning.
        
        PSI = sum((Actual_i - Expected_i) * ln(Actual_i / Expected_i))
        Interpretation:
          < 0.10: NO_DRIFT (Stable population)
          0.10 - 0.25: WARNING (Moderate shift)
          > 0.25: DRIFT (Significant drift, requires model retraining)
        """
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]

        if len(baseline) == 0 or len(current) == 0:
            return 0.0

        # Calculate quantiles from baseline
        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(baseline, quantiles)
        bins[0] = -np.inf
        bins[-1] = np.inf

        # Calculate frequencies
        base_counts, _ = np.histogram(baseline, bins=bins)
        curr_counts, _ = np.histogram(current, bins=bins)

        # Convert to proportions with smoothing epsilon to prevent division by zero
        eps = 1e-6
        base_props = (base_counts + eps) / (len(baseline) + eps * num_buckets)
        curr_props = (curr_counts + eps) / (len(current) + eps * num_buckets)

        # Compute PSI sum
        psi_value = np.sum((curr_props - base_props) * np.log(curr_props / base_props))
        return round(float(max(0.0, psi_value)), 4)

    @staticmethod
    def calculate_ks_test(baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
        """Kolmogorov-Smirnov 2-sample test for continuous distribution differences.
        
        Returns:
            (ks_statistic, p_value)
        """
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]
        if len(baseline) == 0 or len(current) == 0:
            return 0.0, 1.0

        res = stats.ks_2samp(baseline, current)
        return round(float(res.statistic), 4), round(float(res.pvalue), 6)

    @staticmethod
    def analyze_dataset_drift(
        db: Session,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        model_id: Optional[str] = None,
        feature_columns: Optional[List[str]] = None,
    ) -> List[AdvancedDataDriftReport]:
        """Execute PSI and KS tests across all numerical features and persist reports."""
        cols = feature_columns or [c for c in baseline_df.columns if c in current_df.columns and pd.api.types.is_numeric_dtype(baseline_df[c])]
        reports: List[AdvancedDataDriftReport] = []

        for col in cols:
            b_vals = baseline_df[col].dropna().values
            c_vals = current_df[col].dropna().values
            if len(b_vals) < 10 or len(c_vals) < 10:
                continue

            psi_score = StatisticalDriftService.calculate_psi(b_vals, c_vals)
            ks_stat, p_val = StatisticalDriftService.calculate_ks_test(b_vals, c_vals)

            status = "DRIFT" if psi_score >= 0.25 else "WARNING" if psi_score >= 0.10 else "NO_DRIFT"

            report = AdvancedDataDriftReport(
                model_id=model_id,
                feature_name=col,
                drift_method="PSI",
                drift_score=psi_score,
                threshold=0.10,
                status=status,
                baseline_stats_json=json.dumps({
                    "mean": round(float(np.mean(b_vals)), 2),
                    "std": round(float(np.std(b_vals)), 2),
                    "min": round(float(np.min(b_vals)), 2),
                    "max": round(float(np.max(b_vals)), 2),
                }),
                current_stats_json=json.dumps({
                    "mean": round(float(np.mean(c_vals)), 2),
                    "std": round(float(np.std(c_vals)), 2),
                    "min": round(float(np.min(c_vals)), 2),
                    "max": round(float(np.max(c_vals)), 2),
                    "ks_statistic": ks_stat,
                    "p_value": p_val,
                }),
            )
            reports.append(report)
            db.add(report)

        db.commit()
        return reports

    @staticmethod
    def evaluate_model_drift(
        db: Session,
        model_version_id: str,
        current_accuracy: float,
        current_f1: float,
    ) -> ModelDriftReport:
        """Compare active production model metrics against registration baseline."""
        version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()
        if not version:
            raise ValueError(f"Model version {model_version_id} not found")

        baseline_acc = version.accuracy or 0.88
        baseline_f1 = version.f1 or 0.85

        acc_drop = round(baseline_acc - current_accuracy, 4)
        f1_drop = round(baseline_f1 - current_f1, 4)

        status = "CRITICAL" if (acc_drop > 0.08 or f1_drop > 0.08) else "DEGRADED" if (acc_drop > 0.04 or f1_drop > 0.04) else "STABLE"

        drift_rep = ModelDriftReport(
            model_version_id=model_version_id,
            baseline_accuracy=baseline_acc,
            current_accuracy=current_accuracy,
            accuracy_drop=acc_drop,
            baseline_f1=baseline_f1,
            current_f1=current_f1,
            f1_drop=f1_drop,
            status=status,
            alert_triggered=status in ("DEGRADED", "CRITICAL"),
        )
        db.add(drift_rep)
        db.commit()
        db.refresh(drift_rep)
        return drift_rep
