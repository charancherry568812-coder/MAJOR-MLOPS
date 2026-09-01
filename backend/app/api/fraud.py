"""Fraud Detection and Transaction Risk API Router."""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.bank import Bank
from app.models.fraud import FraudAlert, Transaction
from app.schemas.common import paginated_response
from app.schemas.fraud import (
    FraudAlertResponse,
    FraudSummaryResponse,
    ResolveAlertRequest,
    TransactionScoreRequest,
    TransactionScoreResponse,
)
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


def _calculate_fraud_probability(data: TransactionScoreRequest) -> tuple[float, str, bool, str, dict]:
    """Calculate fraud probability based on transaction behavioral metrics."""
    # Weights for risk factors
    prob = (
        0.30 * min(data.amount_deviation / 8.0, 1.0)
        + 0.25 * (data.velocity_score / 100.0)
        + 0.15 * min(data.amount / 20000.0, 1.0)
        + 0.15 * (1.0 if data.num_devices > 2 else 0.2)
        + 0.15 * (1.0 - min(data.account_age_months / 120.0, 1.0))
    )
    prob = round(float(min(max(prob, 0.01), 0.99)), 4)

    reasons = []
    if data.amount_deviation > 3.0:
        reasons.append(f"Amount is {data.amount_deviation:.1f}x typical customer average")
    if data.velocity_score > 70.0:
        reasons.append("Abnormally rapid velocity of transactions within a short window")
    if data.num_devices > 2:
        reasons.append(f"Multiple devices ({data.num_devices}) accessing account simultaneously")
    if data.amount > 10000.0:
        reasons.append("High monetary value exceeding AML standard thresholds")

    flag_reason = " | ".join(reasons) if reasons else "Transaction patterns within nominal parameters"

    if prob >= 0.70:
        risk_level = "HIGH"
        is_flagged = True
        recommendation = "REJECT or place on IMMEDIATE SECURITY HOLD pending biometric 2FA"
    elif prob >= 0.40:
        risk_level = "MEDIUM"
        is_flagged = True
        recommendation = "STEP-UP AUTHENTICATION: Require SMS OTP or branch verification"
    else:
        risk_level = "LOW"
        is_flagged = False
        recommendation = "APPROVE: Transaction risk is well within normal tolerance"

    features = {
        "amount_deviation": round(0.30 * min(data.amount_deviation / 8.0, 1.0), 3),
        "velocity_score": round(0.25 * (data.velocity_score / 100.0), 3),
        "transaction_amount": round(0.15 * min(data.amount / 20000.0, 1.0), 3),
        "device_multiplicity": round(0.15 * (1.0 if data.num_devices > 2 else 0.2), 3),
        "account_tenure": round(0.15 * (1.0 - min(data.account_age_months / 120.0, 1.0)), 3),
    }

    return prob, risk_level, is_flagged, flag_reason, recommendation, features


@router.post("/score-transaction", response_model=TransactionScoreResponse)
def score_transaction(
    req: TransactionScoreRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Real-time transaction scoring and fraud evaluation."""
    prob, risk_level, is_flagged, flag_reason, recommendation, features = _calculate_fraud_probability(req)

    ref = f"TXN-{random.randint(10000, 99999)}"
    now = datetime.now(timezone.utc)

    # Determine bank
    bank_id = req.bank_id
    if not bank_id:
        first_bank = db.query(Bank).filter(Bank.is_deleted == False).first()
        bank_id = first_bank.id if first_bank else None

    # Persist transaction
    txn = Transaction(
        transaction_reference=ref,
        customer_id=req.customer_id,
        bank_id=bank_id,
        amount=req.amount,
        transaction_type=req.transaction_type,
        merchant_category=req.merchant_category,
        velocity_score=req.velocity_score,
        amount_deviation=req.amount_deviation,
        num_devices=req.num_devices,
        fraud_score=prob,
        risk_level=risk_level,
        is_flagged=is_flagged,
        created_at=now,
    )
    db.add(txn)
    db.flush()

    alert_code = None
    alert_id = None
    if is_flagged:
        alert_code = f"ALT-{str(uuid.uuid4())[:8].upper()}"
        alert = FraudAlert(
            alert_code=alert_code,
            transaction_id=txn.id,
            bank_id=bank_id,
            customer_id=req.customer_id,
            risk_score=req.velocity_score,
            fraud_probability=prob,
            severity="CRITICAL" if risk_level == "HIGH" else "HIGH",
            status="OPEN",
            flag_reason=flag_reason,
            created_at=now,
        )
        db.add(alert)
        db.flush()
        alert_id = alert.id
        create_audit_log(
            db,
            "FRAUD_ALERT_CREATED",
            resource_type="fraud_alert",
            resource_id=alert.id,
            user=current_user,
            details={"transaction_ref": ref, "probability": prob, "risk_level": risk_level},
        )

    db.commit()

    return TransactionScoreResponse(
        transaction_reference=ref,
        customer_id=req.customer_id,
        amount=req.amount,
        fraud_probability=prob,
        risk_level=risk_level,
        is_flagged=is_flagged,
        recommendation=recommendation,
        flag_reason=flag_reason if is_flagged else None,
        alert_code=alert_code,
        alert_id=alert_id,
        feature_contributions=features,
        timestamp=now.isoformat(),
    )


@router.get("/summary", response_model=FraudSummaryResponse)
def fraud_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Fraud detection dashboard statistics."""
    total_txns = db.query(Transaction).count()
    suspicious = db.query(Transaction).filter(Transaction.is_flagged == True).count()
    open_alerts = db.query(FraudAlert).filter(FraudAlert.status == "OPEN").count()
    resolved_alerts = db.query(FraudAlert).filter(FraudAlert.status == "RESOLVED").count()
    critical_alerts = db.query(FraudAlert).filter(FraudAlert.severity == "CRITICAL", FraudAlert.status == "OPEN").count()

    fraud_rate = round(float(suspicious / total_txns), 4) if total_txns > 0 else 0.0

    return FraudSummaryResponse(
        total_transactions=total_txns,
        suspicious_transactions=suspicious,
        fraud_rate=fraud_rate,
        open_alerts=open_alerts,
        resolved_alerts=resolved_alerts,
        critical_alerts=critical_alerts,
    )


@router.get("/alerts")
def list_fraud_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List fraud alerts with filtering and pagination."""
    query = db.query(FraudAlert)
    if status_filter:
        query = query.filter(FraudAlert.status == status_filter)
    if severity:
        query = query.filter(FraudAlert.severity == severity)

    total = query.count()
    alerts = query.order_by(FraudAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for a in alerts:
        bank = db.query(Bank).filter(Bank.id == a.bank_id).first() if a.bank_id else None
        items.append({
            "id": a.id,
            "alert_code": a.alert_code,
            "transaction_id": a.transaction_id,
            "bank_id": a.bank_id,
            "bank_name": bank.name if bank else "Consortium Bank",
            "customer_id": a.customer_id,
            "risk_score": a.risk_score,
            "fraud_probability": a.fraud_probability,
            "severity": a.severity,
            "status": a.status,
            "flag_reason": a.flag_reason,
            "resolution_notes": a.resolution_notes,
            "resolved_by": a.resolved_by,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}


@router.put("/alerts/{alert_id}/resolve")
def resolve_fraud_alert(
    alert_id: str,
    req: ResolveAlertRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "SUPER_ADMIN", "BANK_ADMIN", "ML_ENGINEER", "AUDITOR"])),
):
    """Resolve or reject a suspicious transaction fraud alert."""
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Fraud alert not found")

    now = datetime.now(timezone.utc)
    new_status = req.action.upper()
    if new_status not in ("RESOLVED", "REJECTED"):
        new_status = "RESOLVED"

    alert.status = new_status
    alert.resolution_notes = req.resolution_notes
    alert.resolved_by = current_user.id
    alert.resolved_at = now

    db.commit()

    create_audit_log(
        db,
        "FRAUD_ALERT_RESOLVED",
        resource_type="fraud_alert",
        resource_id=alert.id,
        user=current_user,
        details={"alert_code": alert.alert_code, "action": new_status, "notes": req.resolution_notes},
    )

    return {"success": True, "data": {"id": alert.id, "alert_code": alert.alert_code, "status": alert.status}}


@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    flagged_only: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List transactions scored for fraud."""
    query = db.query(Transaction)
    if flagged_only is not None:
        query = query.filter(Transaction.is_flagged == flagged_only)

    total = query.count()
    txns = query.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for t in txns:
        bank = db.query(Bank).filter(Bank.id == t.bank_id).first() if t.bank_id else None
        items.append({
            "id": t.id,
            "transaction_reference": t.transaction_reference,
            "customer_id": t.customer_id,
            "bank_name": bank.name if bank else "Consortium Bank",
            "amount": t.amount,
            "transaction_type": t.transaction_type,
            "merchant_category": t.merchant_category,
            "velocity_score": t.velocity_score,
            "amount_deviation": t.amount_deviation,
            "fraud_score": t.fraud_score,
            "risk_level": t.risk_level,
            "is_flagged": t.is_flagged,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}
