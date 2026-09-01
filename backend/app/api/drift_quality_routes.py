"""Data Drift (PSI/KS), Model Drift, Concept Drift, and Data Quality API Router."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.dataset import Dataset, DatasetVersion, DataQualityReport
from app.models.drift_quality import AdvancedDataDriftReport, ModelDriftReport, ConceptDriftReport
from app.services.drift_service import StatisticalDriftService

drift_router = APIRouter(prefix="/data-drift", tags=["Data Drift & Quality"])
quality_router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


@drift_router.get("/psi")
def list_psi_drift_reports(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reports = db.query(AdvancedDataDriftReport).order_by(AdvancedDataDriftReport.created_at.desc()).all()
    items = []
    for r in reports:
        curr_stats = json.loads(r.current_stats_json) if r.current_stats_json else {}
        base_stats = json.loads(r.baseline_stats_json) if r.baseline_stats_json else {}
        items.append({
            "id": r.id,
            "feature_name": r.feature_name,
            "drift_method": r.drift_method,
            "drift_score": r.drift_score,
            "threshold": r.threshold,
            "status": r.status,
            "ks_statistic": curr_stats.get("ks_statistic"),
            "p_value": curr_stats.get("p_value"),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"success": True, "data": items}


@drift_router.post("/calculate")
def trigger_statistical_drift(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Calculate true PSI and Kolmogorov-Smirnov statistics using local bank datasets."""
    data_dir = Path("dataset_storage").resolve()
    f1 = data_dir / "bank-001_customers.csv"
    f2 = data_dir / "bank-002_customers.csv"

    if not f1.exists() or not f2.exists():
        raise HTTPException(status_code=404, detail="Datasets not found in storage")

    df1 = pd.read_csv(f1)
    df2 = pd.read_csv(f2)

    reports = StatisticalDriftService.analyze_dataset_drift(
        db=db,
        baseline_df=df1,
        current_df=df2,
    )

    return {
        "success": True,
        "data": {
            "features_analyzed": len(reports),
            "drifted_features": sum(1 for r in reports if r.status == "DRIFT"),
            "warning_features": sum(1 for r in reports if r.status == "WARNING"),
            "reports": [{
                "feature": r.feature_name,
                "psi_score": r.drift_score,
                "status": r.status,
            } for r in reports],
        },
    }


@quality_router.get("/reports")
def list_quality_reports(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reports = db.query(DataQualityReport).order_by(DataQualityReport.created_at.desc()).all()
    return {"success": True, "data": [{
        "id": q.id,
        "dataset_version_id": q.dataset_version_id,
        "overall_score": q.overall_score,
        "completeness_score": q.completeness_score,
        "validity_score": q.validity_score,
        "uniqueness_score": q.uniqueness_score,
        "consistency_score": q.consistency_score,
        "missing_count": q.missing_count,
        "duplicate_count": q.duplicate_count,
        "outlier_count": q.outlier_count,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    } for q in reports]}
