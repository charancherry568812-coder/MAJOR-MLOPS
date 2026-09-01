"""Datasets API router."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_user_bank_ids
from app.core.config import get_settings
from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.bank import Bank
from app.models.dataset import Dataset, DatasetVersion, DataQualityReport
from app.schemas.common import paginated_response
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def _analyze_quality(df: pd.DataFrame) -> dict:
    """Analyze dataset quality."""
    total_cells = df.shape[0] * df.shape[1]
    missing = int(df.isnull().sum().sum())
    duplicates = int(df.duplicated().sum())
    missing_pct = (missing / total_cells * 100) if total_cells > 0 else 0
    dup_pct = (duplicates / len(df) * 100) if len(df) > 0 else 0

    # Quality score: start at 100, deduct for issues
    score = 100.0
    score -= min(30, missing_pct * 2)
    score -= min(20, dup_pct * 2)
    score = max(0, score)

    # Missing values per column
    missing_report = {}
    for col in df.columns:
        m = int(df[col].isnull().sum())
        if m > 0:
            missing_report[col] = {"count": m, "percentage": round(m / len(df) * 100, 2)}

    # Outliers (IQR method for numeric columns)
    outlier_report = {}
    for col in df.select_dtypes(include="number").columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((df[col] < lower) | (df[col] > upper)).sum())
        if outliers > 0:
            outlier_report[col] = {"count": outliers, "percentage": round(outliers / len(df) * 100, 2)}

    # Class distribution for common targets
    class_dist = {}
    for target in ["is_default", "is_fraud", "churn_label", "aml_flag"]:
        if target in df.columns:
            class_dist[target] = df[target].value_counts().to_dict()

    # Statistics
    stats = {}
    for col in df.select_dtypes(include="number").columns:
        stats[col] = {
            "mean": round(float(df[col].mean()), 4),
            "std": round(float(df[col].std()), 4),
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "median": round(float(df[col].median()), 4),
        }

    recommendations = []
    if missing_pct > 5:
        recommendations.append("Consider imputing missing values - significant missing data detected")
    if dup_pct > 2:
        recommendations.append("Remove duplicate records before training")
    if outlier_report:
        recommendations.append("Review outlier values in numeric features")

    return {
        "missing_value_report": missing_report,
        "duplicate_report": {"total": duplicates, "percentage": round(dup_pct, 2)},
        "outlier_report": outlier_report,
        "class_distribution": class_dist,
        "statistics": stats,
        "overall_score": round(score, 1),
        "recommendations": recommendations,
    }


@router.get("")
def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bank_id: Optional[str] = None,
    use_case: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Dataset).filter(Dataset.is_deleted == False)

    # Bank-scoped access
    bank_ids = get_user_bank_ids(db, current_user)
    if bank_ids is not None:
        query = query.filter(Dataset.bank_id.in_(bank_ids))

    if bank_id:
        query = query.filter(Dataset.bank_id == bank_id)
    if use_case:
        query = query.filter(Dataset.use_case == use_case)
    if status_filter:
        query = query.filter(Dataset.status == status_filter)
    if search:
        query = query.filter(Dataset.name.ilike(f"%{search}%"))

    total = query.count()
    datasets = query.order_by(Dataset.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for d in datasets:
        bank = db.query(Bank).filter(Bank.id == d.bank_id).first()
        latest_version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == d.id).order_by(DatasetVersion.created_at.desc()).first()
        items.append({
            "id": d.id, "name": d.name, "bank_id": d.bank_id,
            "bank_name": bank.name if bank else "", "description": d.description,
            "use_case": d.use_case, "file_size": d.file_size, "status": d.status,
            "current_version": latest_version.version if latest_version else "v1.0",
            "rows": latest_version.rows if latest_version else 0,
            "features": latest_version.features if latest_version else 0,
            "missing_values": latest_version.missing_values if latest_version else 0,
            "duplicates": latest_version.duplicates if latest_version else 0,
            "quality_score": latest_version.quality_score if latest_version else 0.0,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}


@router.post("/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    bank_id: str = Query(...),
    name: str = Query(...),
    use_case: str = Query(default="credit_risk"),
    description: str = Query(default=""),
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "ML_ENGINEER", "DATA_SCIENTIST"])),
):
    """Upload a CSV dataset."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    settings = get_settings()
    storage_dir = Path(settings.DATASET_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = storage_dir / f"{file_id}.csv"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    dataset = Dataset(
        name=name, bank_id=bank_id, description=description,
        file_path=str(file_path), file_size=len(content),
        use_case=use_case, status="UPLOADED", created_by=current_user.id,
    )
    db.add(dataset)
    db.flush()

    # Create initial version
    quality = _analyze_quality(df)
    version = DatasetVersion(
        dataset_id=dataset.id, version="v1.0",
        rows=len(df), features=len(df.columns),
        feature_names=json.dumps(list(df.columns)),
        missing_values=int(df.isnull().sum().sum()),
        duplicates=int(df.duplicated().sum()),
        quality_score=quality["overall_score"],
        schema_info=json.dumps({col: str(df[col].dtype) for col in df.columns}),
        statistics=json.dumps(quality["statistics"]),
        class_distribution=json.dumps(quality["class_distribution"]),
    )
    db.add(version)
    db.flush()

    # Create quality report
    qr = DataQualityReport(
        dataset_version_id=version.id,
        missing_value_report=json.dumps(quality["missing_value_report"]),
        duplicate_report=json.dumps(quality["duplicate_report"]),
        outlier_report=json.dumps(quality["outlier_report"]),
        class_imbalance_report=json.dumps(quality["class_distribution"]),
        overall_score=quality["overall_score"],
        recommendations=json.dumps(quality["recommendations"]),
    )
    db.add(qr)
    dataset.status = "VALIDATED"
    db.commit()

    create_audit_log(db, "UPLOAD", "dataset", dataset.id, current_user, {"name": name, "rows": len(df)})

    return {"success": True, "data": {
        "id": dataset.id, "name": dataset.name, "rows": len(df),
        "features": len(df.columns), "quality_score": quality["overall_score"],
        "status": dataset.status,
    }}


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_deleted == False).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    bank = db.query(Bank).filter(Bank.id == dataset.bank_id).first()
    versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.created_at.desc()).all()
    latest = versions[0] if versions else None

    version_list = []
    for v in versions:
        qr = db.query(DataQualityReport).filter(DataQualityReport.dataset_version_id == v.id).first()
        version_list.append({
            "id": v.id, "version": v.version, "rows": v.rows, "features": v.features,
            "missing_values": v.missing_values, "duplicates": v.duplicates,
            "quality_score": v.quality_score,
            "feature_names": json.loads(v.feature_names) if v.feature_names else [],
            "statistics": json.loads(v.statistics) if v.statistics else {},
            "schema_info": json.loads(v.schema_info) if v.schema_info else {},
            "quality_report": {
                "overall_score": qr.overall_score if qr else 0,
                "missing_value_report": json.loads(qr.missing_value_report) if qr else {},
                "duplicate_report": json.loads(qr.duplicate_report) if qr else {},
                "outlier_report": json.loads(qr.outlier_report) if qr else {},
                "recommendations": json.loads(qr.recommendations) if qr else [],
            } if qr else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    return {"success": True, "data": {
        "id": dataset.id, "name": dataset.name, "bank_id": dataset.bank_id,
        "bank_name": bank.name if bank else "", "description": dataset.description,
        "use_case": dataset.use_case, "file_size": dataset.file_size, "status": dataset.status,
        "versions": version_list,
        "current_version": latest.version if latest else "v1.0",
        "rows": latest.rows if latest else 0,
        "features": latest.features if latest else 0,
        "quality_score": latest.quality_score if latest else 0.0,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
    }}


@router.post("/{dataset_id}/validate")
def validate_dataset(dataset_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")

    df = pd.read_csv(dataset.file_path)
    quality = _analyze_quality(df)
    dataset.status = "VALIDATED"
    db.commit()

    return {"success": True, "data": {"status": "VALIDATED", "quality_score": quality["overall_score"],
            "recommendations": quality["recommendations"]}}


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN"]))):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.is_deleted = True
    db.commit()
    create_audit_log(db, "DELETE", "dataset", dataset_id, current_user)
    return {"success": True, "message": "Dataset deleted"}


@router.post("/generate-demo")
def generate_demo_data(
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN"])),
):
    """Generate synthetic banking demo data for all banks."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

    try:
        from scripts.generate_data import generate_all_datasets
    except ImportError:
        raise HTTPException(status_code=500, detail="Data generator not found")

    settings = get_settings()
    output_dir = Path(settings.DATASET_STORAGE_PATH)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = generate_all_datasets(str(output_dir))

    # Register generated datasets in DB
    banks = db.query(Bank).filter(Bank.is_deleted == False).all()
    bank_map = {b.code: b for b in banks}

    results = []
    for gen_info in generated:
        bank_code = gen_info["bank_code"]
        bank = bank_map.get(bank_code)
        if not bank:
            continue

        df = pd.read_csv(gen_info["file_path"])
        quality = _analyze_quality(df)

        dataset = Dataset(
            name=f"{bank.name} - Demo Dataset",
            bank_id=bank.id, description=f"Auto-generated demo dataset for {bank.name}",
            file_path=gen_info["file_path"], file_size=os.path.getsize(gen_info["file_path"]),
            use_case="credit_risk", status="VALIDATED", created_by=current_user.id,
        )
        db.add(dataset)
        db.flush()

        version = DatasetVersion(
            dataset_id=dataset.id, version="v1.0",
            rows=len(df), features=len(df.columns),
            feature_names=json.dumps(list(df.columns)),
            missing_values=int(df.isnull().sum().sum()),
            duplicates=int(df.duplicated().sum()),
            quality_score=quality["overall_score"],
            schema_info=json.dumps({col: str(df[col].dtype) for col in df.columns}),
            statistics=json.dumps(quality["statistics"]),
            class_distribution=json.dumps(quality["class_distribution"]),
        )
        db.add(version)
        db.flush()

        qr = DataQualityReport(
            dataset_version_id=version.id,
            missing_value_report=json.dumps(quality["missing_value_report"]),
            duplicate_report=json.dumps(quality["duplicate_report"]),
            outlier_report=json.dumps(quality["outlier_report"]),
            class_imbalance_report=json.dumps(quality["class_distribution"]),
            overall_score=quality["overall_score"],
            recommendations=json.dumps(quality["recommendations"]),
        )
        db.add(qr)
        results.append({"bank": bank.name, "rows": len(df), "quality_score": quality["overall_score"]})

    db.commit()
    create_audit_log(db, "CREATE", "dataset", None, current_user, {"action": "generate_demo_data", "count": len(results)})

    return {"success": True, "data": {"generated": results, "total_banks": len(results)}}
