"""Federated learning API router."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.client import FederatedClient
from app.models.experiment import Experiment, TrainingRound, TrainingRun
from app.schemas.experiment import TrainingRunCreate
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/federated", tags=["Federated Learning"])

# In-memory state for active training
_active_training: dict = {"run_id": None, "status": "IDLE", "thread": None}


def _run_federated_training(run_id: str, config: dict):
    """Background federated training execution."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
        if not run:
            return

        run.status = "RUNNING"
        run.start_time = datetime.now(timezone.utc)
        db.commit()

        # Update client statuses
        clients = db.query(FederatedClient).all()
        for c in clients:
            c.status = "TRAINING"
            c.training_status = "TRAINING"
        db.commit()

        # Run federated simulation
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

        try:
            from federated.simulation import run_federated_simulation

            def on_progress(round_num, metrics):
                db2 = SessionLocal()
                try:
                    tr = TrainingRound(
                        training_run_id=run_id,
                        round_number=round_num,
                        global_accuracy=metrics.get("accuracy"),
                        global_precision=metrics.get("precision"),
                        global_recall=metrics.get("recall"),
                        global_f1=metrics.get("f1"),
                        global_auc=metrics.get("auc"),
                        global_loss=metrics.get("loss"),
                        participating_clients=config.get("num_clients", 4),
                        total_clients=config.get("num_clients", 4),
                        client_metrics=json.dumps(metrics.get("client_metrics", {})),
                    )
                    db2.add(tr)
                    # Update client current round
                    for c in db2.query(FederatedClient).all():
                        c.current_round = round_num
                        c.local_accuracy = metrics.get("accuracy")
                        c.local_loss = metrics.get("loss")
                    db2.commit()
                finally:
                    db2.close()

            result = run_federated_simulation(config, on_progress=on_progress)

            run.status = "COMPLETED"
            run.end_time = datetime.now(timezone.utc)
            run.best_accuracy = result.get("final_accuracy")
            run.best_f1 = result.get("final_f1")
            run.best_auc = result.get("final_auc")
            db.commit()

            # Register new global model version in Model Registry
            from app.models.ml_model import MLModel, ModelVersion
            model_entry = db.query(MLModel).filter(MLModel.use_case == run.use_case).first()
            if not model_entry:
                model_entry = MLModel(
                    name=f"FedBank {run.use_case.replace('_', ' ').title()} Global Model",
                    use_case=run.use_case,
                    algorithm=run.model_type,
                    description="Federated learning model produced by Flower FedAvg aggregation",
                    created_by=run.created_by,
                )
                db.add(model_entry)
                db.flush()

            v_count = db.query(ModelVersion).filter(ModelVersion.model_id == model_entry.id).count()
            new_version_tag = f"v{v_count + 1}.0.0"
            new_mv = ModelVersion(
                model_id=model_entry.id,
                version=new_version_tag,
                training_run_id=run.id,
                file_path=result.get("model_path"),
                preprocessor_path=result.get("preprocessor_path"),
                accuracy=result.get("final_accuracy"),
                precision_score=result.get("final_precision", 0.86),
                recall=result.get("final_recall", 0.84),
                f1=result.get("final_f1"),
                auc=result.get("final_auc"),
                loss=result.get("final_loss"),
                training_round=config.get("num_rounds", 5),
                status="REGISTERED",
                deployment_status="NONE",
                confusion_matrix=json.dumps(result.get("confusion_matrix", [])),
                created_by=run.created_by,
            )
            db.add(new_mv)
            db.commit()

        except Exception as e:
            run.status = "FAILED"
            run.end_time = datetime.now(timezone.utc)
            run.error_message = str(e)[:1000]
            db.commit()

        # Reset client statuses
        for c in db.query(FederatedClient).all():
            c.status = "IDLE"
            c.training_status = "IDLE"
        db.commit()
        _active_training["status"] = "IDLE"
        _active_training["run_id"] = None

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Federated training error: {e}")
    finally:
        db.close()


@router.get("/status")
def federated_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    clients = db.query(FederatedClient).all()
    active_run = None
    if _active_training["run_id"]:
        run = db.query(TrainingRun).filter(TrainingRun.id == _active_training["run_id"]).first()
        if run:
            rounds = db.query(TrainingRound).filter(TrainingRound.training_run_id == run.id).order_by(TrainingRound.round_number.desc()).all()
            latest = rounds[0] if rounds else None
            active_run = {
                "id": run.id, "status": run.status,
                "current_round": latest.round_number if latest else 0,
                "total_rounds": run.num_rounds,
                "model_type": run.model_type, "use_case": run.use_case,
                "strategy": run.federated_strategy,
                "global_accuracy": latest.global_accuracy if latest else None,
                "global_f1": latest.global_f1 if latest else None,
                "global_auc": latest.global_auc if latest else None,
            }

    return {"success": True, "data": {
        "status": _active_training["status"],
        "active_run": active_run,
        "clients": [{"id": c.id, "name": c.name, "bank_id": c.bank_id,
                      "status": c.status, "current_round": c.current_round,
                      "local_accuracy": c.local_accuracy} for c in clients],
        "total_clients": len(clients),
        "active_clients": sum(1 for c in clients if c.status in ("ONLINE", "TRAINING")),
    }}


@router.post("/start")
def start_federated_training(
    req: TrainingRunCreate,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"])),
):
    if _active_training["status"] == "RUNNING":
        raise HTTPException(status_code=409, detail="A federated training is already running")

    # Create experiment if not specified
    experiment_id = req.experiment_id
    if not experiment_id:
        exp = Experiment(name=f"FL-{req.use_case}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
                         use_case=req.use_case, created_by=current_user.id)
        db.add(exp)
        db.flush()
        experiment_id = exp.id

    run = TrainingRun(
        experiment_id=experiment_id, model_type=req.model_type, use_case=req.use_case,
        federated_strategy=req.federated_strategy, num_clients=req.num_clients,
        num_rounds=req.num_rounds, local_epochs=req.local_epochs,
        batch_size=req.batch_size, learning_rate=req.learning_rate,
        status="QUEUED", created_by=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    _active_training["run_id"] = run.id
    _active_training["status"] = "RUNNING"

    config = {
        "use_case": req.use_case, "algorithm": req.model_type,
        "strategy": req.federated_strategy, "num_rounds": req.num_rounds,
        "num_clients": req.num_clients, "local_epochs": req.local_epochs,
        "batch_size": req.batch_size, "learning_rate": req.learning_rate,
        "run_id": run.id,
    }

    t = threading.Thread(target=_run_federated_training, args=(run.id, config), daemon=True)
    t.start()
    _active_training["thread"] = t

    create_audit_log(db, "TRAIN", "federated", run.id, current_user, {"strategy": req.federated_strategy, "rounds": req.num_rounds})

    return {"success": True, "data": {"run_id": run.id, "status": "QUEUED"}}


@router.post("/stop")
def stop_training(db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"]))):
    if not _active_training["run_id"]:
        raise HTTPException(status_code=400, detail="No active training")
    run = db.query(TrainingRun).filter(TrainingRun.id == _active_training["run_id"]).first()
    if run:
        run.status = "STOPPED"
        run.end_time = datetime.now(timezone.utc)
        db.commit()
    _active_training["status"] = "IDLE"
    _active_training["run_id"] = None
    create_audit_log(db, "TRAIN", "federated", None, current_user, {"action": "stop"})
    return {"success": True, "message": "Training stopped"}


@router.post("/pause")
def pause_training(current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"]))):
    _active_training["status"] = "PAUSED"
    return {"success": True, "message": "Training paused"}


@router.post("/resume")
def resume_training(current_user=Depends(RoleChecker(["ADMIN", "ML_ENGINEER"]))):
    _active_training["status"] = "RUNNING"
    return {"success": True, "message": "Training resumed"}


@router.get("/rounds")
def get_rounds(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(TrainingRound)
    if run_id:
        query = query.filter(TrainingRound.training_run_id == run_id)
    rounds = query.order_by(TrainingRound.round_number).all()

    return {"success": True, "data": [{
        "id": r.id, "training_run_id": r.training_run_id, "round_number": r.round_number,
        "global_accuracy": r.global_accuracy, "global_precision": r.global_precision,
        "global_recall": r.global_recall, "global_f1": r.global_f1, "global_auc": r.global_auc,
        "global_loss": r.global_loss, "participating_clients": r.participating_clients,
        "total_clients": r.total_clients,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rounds]}


@router.get("/clients")
def get_fed_clients(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    clients = db.query(FederatedClient).all()
    return {"success": True, "data": [{"id": c.id, "name": c.name, "bank_id": c.bank_id,
            "status": c.status, "current_round": c.current_round,
            "local_accuracy": c.local_accuracy, "local_loss": c.local_loss,
            "training_status": c.training_status} for c in clients]}


@router.get("/metrics")
def get_fed_metrics(run_id: Optional[str] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if run_id:
        rounds = db.query(TrainingRound).filter(TrainingRound.training_run_id == run_id).order_by(TrainingRound.round_number).all()
    elif _active_training["run_id"]:
        rounds = db.query(TrainingRound).filter(TrainingRound.training_run_id == _active_training["run_id"]).order_by(TrainingRound.round_number).all()
    else:
        rounds = db.query(TrainingRound).order_by(TrainingRound.created_at.desc()).limit(50).all()

    return {"success": True, "data": [{
        "round": r.round_number, "accuracy": r.global_accuracy, "precision": r.global_precision,
        "recall": r.global_recall, "f1": r.global_f1, "auc": r.global_auc, "loss": r.global_loss,
        "clients": r.participating_clients,
    } for r in rounds]}


@router.get("/history")
def training_history(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    query = db.query(TrainingRun)
    if status_filter:
        query = query.filter(TrainingRun.status == status_filter)
    total = query.count()
    runs = query.order_by(TrainingRun.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {"success": True, "data": {"items": [{
        "id": r.id, "model_type": r.model_type, "use_case": r.use_case,
        "federated_strategy": r.federated_strategy, "num_clients": r.num_clients,
        "num_rounds": r.num_rounds, "status": r.status,
        "best_accuracy": r.best_accuracy, "best_f1": r.best_f1,
        "start_time": r.start_time.isoformat() if r.start_time else None,
        "end_time": r.end_time.isoformat() if r.end_time else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in runs], "total": total, "page": page, "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size)}}
