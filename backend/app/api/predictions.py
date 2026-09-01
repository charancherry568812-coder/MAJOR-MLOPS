"""Predictions API router."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.deployment import Deployment
from app.models.ml_model import MLModel, ModelVersion
from app.models.prediction import Prediction, PredictionBatch
from app.schemas.prediction import PredictionRequest
from app.schemas.common import paginated_response
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/predictions", tags=["Predictions"])

RISK_ROLES = ["SUPER_ADMIN", "ADMIN", "BANK_ADMIN", "ML_ENGINEER", "DATA_SCIENTIST", "ANALYST"]


def _get_production_model(db: Session, use_case: str):
    """Find the currently deployed production model for a use case."""
    versions = db.query(ModelVersion).filter(ModelVersion.status == "PRODUCTION").all()
    for v in versions:
        model = db.query(MLModel).filter(MLModel.id == v.model_id).first()
        if model and model.use_case == use_case:
            return v, model
    return None, None


def _do_prediction(version: ModelVersion, features: dict) -> dict:
    """Run actual model prediction."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

    try:
        from mlops.deployment.model_server import model_server
        if model_server.is_loaded(version.id):
            return model_server.predict(version.id, features)
    except Exception:
        pass

    # Fallback: load model directly
    if version.file_path and os.path.exists(version.file_path):
        import joblib
        from ml.pipeline import Preprocessor
        model = joblib.load(version.file_path)
        preprocessor = None
        if version.preprocessor_path and os.path.exists(version.preprocessor_path):
            try:
                preprocessor = Preprocessor.load(version.preprocessor_path)
            except Exception:
                preprocessor = None

        df = pd.DataFrame([features])
        if preprocessor and hasattr(preprocessor, "transform"):
            X = preprocessor.transform(df)
        elif hasattr(model, "feature_names_in_"):
            X = df.reindex(columns=model.feature_names_in_, fill_value=0.0).values
        else:
            X = df.select_dtypes(include="number").values

        proba = model.predict_proba(X)[0] if hasattr(model, "predict_proba") else [0.5, 0.5]
        pred = model.predict(X)[0]
        probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        risk_score = int(probability * 100)

        if probability >= 0.7:
            risk_category = "HIGH_RISK"
        elif probability >= 0.4:
            risk_category = "MEDIUM_RISK"
        else:
            risk_category = "LOW_RISK"

        # SHAP explanation
        explanation = {}
        try:
            import shap
            explainer = shap.TreeExplainer(model) if hasattr(model, "feature_importances_") else shap.LinearExplainer(model, X)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                sv = shap_values[0]

            feature_names = list(features.keys()) if preprocessor is None else list(features.keys())[:len(sv)]
            explanation = {fn: round(float(sv[i]), 4) for i, fn in enumerate(feature_names) if i < len(sv)}
            explanation = dict(sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:10])
        except Exception:
            # Fallback to feature importance if SHAP fails
            if hasattr(model, "feature_importances_"):
                fi = model.feature_importances_
                feature_names = list(features.keys())[:len(fi)]
                explanation = {fn: round(float(fi[i]), 4) for i, fn in enumerate(feature_names)}
                explanation = dict(sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True)[:10])

        return {
            "prediction": risk_category,
            "probability": round(probability, 4),
            "risk_score": risk_score,
            "risk_category": risk_category,
            "explanation": explanation,
        }

    raise HTTPException(status_code=500, detail="Model file not found")


@router.post("")
@router.post("/single")
@router.post("/predict")
def single_prediction(
    req: PredictionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(RISK_ROLES)),
):
    """Run a single prediction using a deployed model."""
    if req.model_version_id:
        version = db.query(ModelVersion).filter(ModelVersion.id == req.model_version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="Model version not found")
        model_obj = db.query(MLModel).filter(MLModel.id == version.model_id).first()
    else:
        version, model_obj = _get_production_model(db, req.use_case)
        if not version:
            raise HTTPException(status_code=404, detail=f"No production model found for use case: {req.use_case}")

    result = _do_prediction(version, req.features)

    prediction = Prediction(
        model_version_id=version.id, use_case=req.use_case,
        input_data=json.dumps(req.features),
        prediction_result=result["prediction"],
        probability=result["probability"],
        risk_score=result["risk_score"],
        risk_category=result["risk_category"],
        explanation=json.dumps(result.get("explanation", {})),
        created_by=current_user.id,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    create_audit_log(db, "PREDICT", "prediction", prediction.id, current_user, {"use_case": req.use_case})

    return {"success": True, "data": {
        "id": prediction.id, "prediction": result["prediction"],
        "probability": result["probability"], "risk_score": result["risk_score"],
        "risk_category": result["risk_category"],
        "model_version": version.version,
        "explanation": result.get("explanation", {}),
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
    }}


@router.post("/predict/batch")
async def batch_prediction(
    file: UploadFile = File(...),
    use_case: str = Query(default="credit_risk"),
    model_version_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(RISK_ROLES)),
):
    """Run batch predictions from CSV upload."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    settings = get_settings()
    storage = Path(settings.DATASET_STORAGE_PATH) / "batches"
    storage.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    input_path = storage / f"{file_id}_input.csv"
    content = await file.read()
    with open(input_path, "wb") as f:
        f.write(content)

    df = pd.read_csv(input_path)

    if model_version_id:
        version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()
    else:
        version, _ = _get_production_model(db, use_case)

    if not version:
        raise HTTPException(status_code=404, detail="No model available")

    batch = PredictionBatch(
        model_version_id=version.id, use_case=use_case,
        file_path=str(input_path), total_records=len(df),
        status="PROCESSING", created_by=current_user.id,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Process predictions
    results = []
    processed = 0
    for _, row in df.iterrows():
        try:
            features = row.to_dict()
            result = _do_prediction(version, features)
            results.append({**features, **result})
            processed += 1
        except Exception:
            results.append({**row.to_dict(), "prediction": "ERROR", "probability": 0, "risk_score": 0, "risk_category": "ERROR"})
            processed += 1

    result_df = pd.DataFrame(results)
    result_path = storage / f"{file_id}_results.csv"
    result_df.to_csv(result_path, index=False)

    batch.processed_records = processed
    batch.result_file_path = str(result_path)
    batch.status = "COMPLETED"
    batch.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {"success": True, "data": {
        "id": batch.id, "total_records": len(df), "processed_records": processed,
        "status": "COMPLETED", "result_file_path": str(result_path),
    }}


@router.get("")
def prediction_history(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    use_case: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    query = db.query(Prediction)
    if use_case:
        query = query.filter(Prediction.use_case == use_case)

    total = query.count()
    predictions = query.order_by(Prediction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for p in predictions:
        version = db.query(ModelVersion).filter(ModelVersion.id == p.model_version_id).first()
        items.append({
            "id": p.id, "use_case": p.use_case,
            "prediction_result": p.prediction_result,
            "probability": p.probability, "risk_score": p.risk_score,
            "risk_category": p.risk_category,
            "model_version": version.version if version else "",
            "input_data": json.loads(p.input_data) if p.input_data else {},
            "explanation": json.loads(p.explanation) if p.explanation else {},
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}


@router.get("/batches")
def list_batches(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    batches = db.query(PredictionBatch).order_by(PredictionBatch.created_at.desc()).limit(50).all()
    return {"success": True, "data": [{
        "id": b.id, "use_case": b.use_case, "total_records": b.total_records,
        "processed_records": b.processed_records, "status": b.status,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    } for b in batches]}


@router.get("/{prediction_id}")
def get_prediction(prediction_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    p = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prediction not found")
    version = db.query(ModelVersion).filter(ModelVersion.id == p.model_version_id).first()
    return {"success": True, "data": {
        "id": p.id, "use_case": p.use_case, "prediction_result": p.prediction_result,
        "probability": p.probability, "risk_score": p.risk_score, "risk_category": p.risk_category,
        "model_version": version.version if version else "",
        "input_data": json.loads(p.input_data) if p.input_data else {},
        "explanation": json.loads(p.explanation) if p.explanation else {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }}
