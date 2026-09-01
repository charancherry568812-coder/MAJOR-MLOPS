"""AML Transaction Monitoring, SAR Cases, and Sanctions Screening API Router."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.kyc_aml_sanctions import AMLAlert, AMLCase, SanctionsMatch, SanctionsWatchlist
from app.schemas.banking import AMLAlertResolveRequest
from app.services.aml_service import AMLMonitoringService
from app.services.sanctions_service import SanctionsScreeningService

aml_router = APIRouter(prefix="/aml", tags=["AML Compliance"])
sanctions_router = APIRouter(prefix="/sanctions", tags=["Sanctions Screening"])


# ─── AML Routes ──────────────────────────────────────────────
@aml_router.get("/alerts")
def list_aml_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(AMLAlert)
    if status:
        query = query.filter(AMLAlert.status == status.upper())
    if severity:
        query = query.filter(AMLAlert.severity == severity.upper())
    if alert_type:
        query = query.filter(AMLAlert.alert_type == alert_type.upper())

    total = query.count()
    alerts = query.order_by(AMLAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for a in alerts:
        items.append({
            "id": a.id,
            "alert_code": a.alert_code,
            "customer_id": a.customer_id,
            "customer_name": f"{a.customer.first_name} {a.customer.last_name}" if a.customer else "",
            "transaction_id": a.transaction_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "risk_score": a.risk_score,
            "status": a.status,
            "resolution_notes": a.resolution_notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@aml_router.put("/alerts/{alert_id}/resolve")
def resolve_aml_alert(
    alert_id: str,
    req: AMLAlertResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "AUDITOR", "SUPER_ADMIN"])),
):
    try:
        updated = AMLMonitoringService.resolve_alert(
            db=db,
            alert_id=alert_id,
            resolution=req.resolution,
            notes=req.notes,
            reviewer_id=current_user.id,
        )
        return {
            "success": True,
            "data": {
                "id": updated.id,
                "status": updated.status,
                "resolution_notes": updated.resolution_notes,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@aml_router.get("/cases")
def list_aml_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(AMLCase)
    if status:
        query = query.filter(AMLCase.status == status.upper())
    if priority:
        query = query.filter(AMLCase.priority == priority.upper())

    cases = query.order_by(AMLCase.created_at.desc()).all()
    return {"success": True, "data": [{
        "id": c.id,
        "case_number": c.case_number,
        "title": c.title,
        "customer_id": c.customer_id,
        "priority": c.priority,
        "status": c.status,
        "findings_summary": c.findings_summary,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in cases]}


# ─── Sanctions Routes ────────────────────────────────────────
@sanctions_router.get("/watchlist")
def list_sanctions_watchlist(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    SanctionsScreeningService.seed_watchlist_if_empty(db)
    items = db.query(SanctionsWatchlist).filter(SanctionsWatchlist.is_active == True).all()
    return {"success": True, "data": [{
        "id": w.id,
        "entity_name": w.entity_name,
        "entity_type": w.entity_type,
        "country_code": w.country_code,
        "list_source": w.list_source,
        "aliases": w.aliases,
    } for w in items]}


@sanctions_router.post("/screen")
def screen_entity_endpoint(
    name: str = Query(..., min_length=2),
    threshold: float = Query(70.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    matches = SanctionsScreeningService.screen_entity(
        db=db,
        query_name=name,
        threshold=threshold,
    )
    return {
        "success": True,
        "data": {
            "query_name": name,
            "threshold": threshold,
            "total_matches": len(matches),
            "is_flagged": len(matches) > 0,
            "matches": [{
                "id": m.id,
                "match_score": m.match_score,
                "match_type": m.match_type,
                "status": m.status,
                "notes": m.review_notes,
            } for m in matches],
        },
    }
