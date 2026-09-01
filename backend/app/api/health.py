"""Health check API router."""

from __future__ import annotations

import platform
import psutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.dependencies import get_db

router = APIRouter(tags=["Health"])


def _check_db(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "HEALTHY", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "UNHEALTHY", "message": str(e)}


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Basic health check."""
    db_status = _check_db(db)
    overall = "HEALTHY" if db_status["status"] == "HEALTHY" else "DEGRADED"
    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_status,
            "backend": {"status": "HEALTHY"},
        },
    }


@router.get("/health/live")
def liveness():
    """Liveness probe — is the process alive."""
    return {"status": "OK"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe — can the service handle traffic."""
    db_status = _check_db(db)
    if db_status["status"] != "HEALTHY":
        return {"status": "NOT_READY", "services": {"database": db_status}}
    return {"status": "READY"}


@router.get("/health/system")
def system_info():
    """System resource information."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
    except Exception:
        cpu, mem, disk = 0.0, None, None
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent if mem else 0.0,
        "memory_total_gb": round(mem.total / (1024**3), 2) if mem else 0.0,
        "disk_percent": disk.percent if disk else 0.0,
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }
