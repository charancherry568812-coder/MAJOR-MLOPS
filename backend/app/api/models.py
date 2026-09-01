"""Models API router — registry, approval, deployment, comparison."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.deployment import Deployment
from app.models.ml_model import MLModel, ModelMetrics, ModelVersion
from app.schemas.model import ModelApproveRequest, ModelCreate
from app.schemas.common import paginated_response
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("")
def list_models(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    use_case: Optional[str] = None, status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    query = db.query(MLModel)
    if use_case:
        query = query.filter(MLModel.use_case == use_case)
    if search:
        query = query.filter(MLModel.name.ilike(f"%{search}%"))

    total = query.count()
    models = query.order_by(MLModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for m in models:
        versions = db.query(ModelVersion).filter(ModelVersion.model_id == m.id).order_by(ModelVersion.created_at.desc()).all()
        if status_filter:
            versions = [v for v in versions if v.status == status_filter]
        latest = versions[0] if versions else None
        prod = next((v for v in versions if v.status == "PRODUCTION"), None)

        items.append({
            "id": m.id, "name": m.name, "use_case": m.use_case, "algorithm": m.algorithm,
            "description": m.description, "versions_count": len(versions),
            "latest_version": latest.version if latest else None,
            "production_version": prod.version if prod else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}


@router.post("", status_code=201)
def create_model(req: ModelCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"]))):
    model = MLModel(name=req.name, use_case=req.use_case, algorithm=req.algorithm,
                    description=req.description, created_by=current_user.id)
    db.add(model)
    db.commit()
    db.refresh(model)
    create_audit_log(db, "CREATE", "model", model.id, current_user, {"name": req.name})
    return {"success": True, "data": {"id": model.id, "name": model.name}}


@router.get("/compare")
def compare_models(
    ids: str = Query(..., description="Comma-separated model version IDs"),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    version_ids = [i.strip() for i in ids.split(",")]
    versions = db.query(ModelVersion).filter(ModelVersion.id.in_(version_ids)).all()

    result = []
    for v in versions:
        model = db.query(MLModel).filter(MLModel.id == v.model_id).first()
        result.append({
            "id": v.id, "model_id": v.model_id, "model_name": model.name if model else "",
            "version": v.version, "algorithm": model.algorithm if model else "",
            "use_case": model.use_case if model else "",
            "accuracy": v.accuracy, "precision_score": v.precision_score,
            "recall": v.recall, "f1": v.f1, "auc": v.auc,
            "status": v.status,
            "confusion_matrix": json.loads(v.confusion_matrix) if v.confusion_matrix else [],
            "feature_importance": json.loads(v.feature_importance) if v.feature_importance else {},
        })

    return {"success": True, "data": result}


@router.get("/{model_id}")
def get_model(model_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    versions = db.query(ModelVersion).filter(ModelVersion.model_id == model_id).order_by(ModelVersion.created_at.desc()).all()

    return {"success": True, "data": {
        "id": model.id, "name": model.name, "use_case": model.use_case,
        "algorithm": model.algorithm, "description": model.description,
        "versions": [{
            "id": v.id, "version": v.version, "accuracy": v.accuracy,
            "precision_score": v.precision_score, "recall": v.recall, "f1": v.f1, "auc": v.auc,
            "status": v.status, "deployment_status": v.deployment_status,
            "confusion_matrix": json.loads(v.confusion_matrix) if v.confusion_matrix else [],
            "classification_report": json.loads(v.classification_report) if v.classification_report else {},
            "feature_importance": json.loads(v.feature_importance) if v.feature_importance else {},
            "approved_by": v.approved_by, "approved_at": v.approved_at.isoformat() if v.approved_at else None,
            "approval_reason": v.approval_reason,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        } for v in versions],
        "created_at": model.created_at.isoformat() if model.created_at else None,
    }}


@router.post("/{version_id}/approve")
def approve_model(
    version_id: str, req: ModelApproveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN"])),
):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    version.status = "APPROVED"
    version.approved_by = current_user.id
    version.approved_at = datetime.now(timezone.utc)
    version.approval_reason = req.reason
    db.commit()

    create_audit_log(db, "APPROVE", "model_version", version_id, current_user, {"reason": req.reason})
    return {"success": True, "data": {"id": version_id, "status": "APPROVED"}}


@router.post("/{version_id}/deploy")
def deploy_model(
    version_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN"])),
):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")
    if version.status not in ("APPROVED", "STAGING"):
        raise HTTPException(status_code=400, detail="Only approved models can be deployed")

    # Undeploy current production version of same model
    current_prod = db.query(ModelVersion).filter(
        ModelVersion.model_id == version.model_id,
        ModelVersion.status == "PRODUCTION",
    ).all()
    for cp in current_prod:
        cp.status = "ARCHIVED"
        cp.deployment_status = "INACTIVE"
        for dep in db.query(Deployment).filter(Deployment.model_version_id == cp.id, Deployment.status == "ACTIVE").all():
            dep.status = "INACTIVE"

    version.status = "PRODUCTION"
    version.deployment_status = "ACTIVE"

    deployment = Deployment(
        model_version_id=version_id, status="ACTIVE",
        deployed_by=current_user.id, deployed_at=datetime.now(timezone.utc),
    )
    db.add(deployment)
    db.commit()

    # Load model into serving
    if version.file_path and os.path.exists(version.file_path):
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
            from mlops.deployment.model_server import model_server
            model_server.load_model(version_id, version.file_path, version.preprocessor_path)
        except Exception:
            pass

    create_audit_log(db, "DEPLOY", "model_version", version_id, current_user)
    return {"success": True, "data": {"id": version_id, "status": "PRODUCTION", "deployment_id": deployment.id}}


@router.post("/{version_id}/rollback")
def rollback_model(version_id: str, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN"]))):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    version.status = "ARCHIVED"
    version.deployment_status = "ROLLED_BACK"
    for dep in db.query(Deployment).filter(Deployment.model_version_id == version_id, Deployment.status == "ACTIVE").all():
        dep.status = "ROLLED_BACK"
        dep.rolled_back_at = datetime.now(timezone.utc)
        dep.rolled_back_by = current_user.id
    db.commit()

    create_audit_log(db, "ROLLBACK", "model_version", version_id, current_user)
    return {"success": True, "message": "Model rolled back"}


@router.post("/{version_id}/archive")
def archive_model(version_id: str, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"]))):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")
    version.status = "ARCHIVED"
    db.commit()
    return {"success": True, "message": "Model archived"}
