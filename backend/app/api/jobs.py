"""Async Jobs & Background Tasks API Router."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.async_job import AsyncJob
from app.services.async_job_service import async_job_manager

jobs_router = APIRouter(prefix="/jobs", tags=["Async Jobs"])


@jobs_router.get("")
def list_jobs(
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(AsyncJob)
    if job_type:
        query = query.filter(AsyncJob.job_type == job_type.upper())
    if status:
        query = query.filter(AsyncJob.status == status.upper())

    total = query.count()
    jobs = query.order_by(AsyncJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for j in jobs:
        items.append({
            "id": j.id,
            "job_type": j.job_type,
            "title": j.title,
            "status": j.status,
            "progress_percent": j.progress_percent,
            "current_step": j.current_step,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@jobs_router.get("/{job_id}")
def get_job_detail(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    j = db.query(AsyncJob).filter(AsyncJob.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    result_data = None
    if j.result_json:
        try:
            result_data = json.loads(j.result_json)
        except Exception:
            result_data = j.result_json

    return {
        "success": True,
        "data": {
            "id": j.id,
            "job_type": j.job_type,
            "title": j.title,
            "status": j.status,
            "progress_percent": j.progress_percent,
            "current_step": j.current_step,
            "result": result_data,
            "error_message": j.error_message,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        },
    }


@jobs_router.post("/trigger-sample-task")
def trigger_sample_task(
    title: str = "Sample Batch Analysis",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger a sample async background job to demonstrate async architecture."""
    def _sample_work(progress_cb):
        for i in range(1, 6):
            time.sleep(0.3)
            progress_cb(i * 20.0, f"Processing batch chunk {i} of 5")
        return {"processed_items": 1000, "status": "BATCH_COMPLETE"}

    job_id = async_job_manager.submit_job(
        job_type="BATCH_ANALYSIS",
        title=title,
        task_fn=_sample_work,
        created_by=current_user.id,
    )
    return {"success": True, "data": {"job_id": job_id, "status": "QUEUED"}}
