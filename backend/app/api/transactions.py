"""Transaction Ledger & Multi-Rail Payment API Router."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.account import Account
from app.models.transaction_payment import Transaction, Payment, UPIPaymentIntent
from app.schemas.banking import TransferRequest, UPIIntentCreateRequest
from app.services.banking_service import BankingService
from app.services.aml_service import AMLMonitoringService
from app.services.sanctions_service import SanctionsScreeningService

transactions_router = APIRouter(prefix="/transactions", tags=["Transactions"])
payments_router = APIRouter(prefix="/payments", tags=["Payments"])


@transactions_router.get("")
def list_transactions(
    rail: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Transaction)
    if rail:
        query = query.filter(Transaction.payment_rail == rail.upper())
    if status:
        query = query.filter(Transaction.status == status.upper())
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Transaction.transaction_reference.ilike(term)) |
            (Transaction.description.ilike(term))
        )

    total = query.count()
    txns = query.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for t in txns:
        items.append({
            "id": t.id,
            "reference": t.transaction_reference,
            "source_account_id": t.source_account_id,
            "destination_account_id": t.destination_account_id,
            "amount": t.amount,
            "currency": t.currency,
            "fee_amount": t.fee_amount,
            "fx_rate": t.fx_rate,
            "settlement_amount": t.settlement_amount,
            "settlement_currency": t.settlement_currency,
            "payment_rail": t.payment_rail,
            "status": t.status,
            "risk_score": t.risk_score,
            "fraud_score": t.fraud_score,
            "is_flagged_fraud": t.is_flagged_fraud,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@transactions_router.get("/{transaction_id}")
def get_transaction_detail(transaction_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    t = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")

    payment_data = None
    if t.payment_record:
        p = t.payment_record
        payment_data = {
            "payment_reference": p.payment_reference,
            "sender_name": p.sender_name,
            "sender_identifier": p.sender_identifier,
            "receiver_name": p.receiver_name,
            "receiver_identifier": p.receiver_identifier,
            "provider_name": p.provider_name,
            "provider_status": p.provider_status,
            "is_sandbox": p.is_sandbox,
        }

    return {
        "success": True,
        "data": {
            "id": t.id,
            "reference": t.transaction_reference,
            "amount": t.amount,
            "currency": t.currency,
            "fee_amount": t.fee_amount,
            "payment_rail": t.payment_rail,
            "status": t.status,
            "risk_score": t.risk_score,
            "fraud_score": t.fraud_score,
            "description": t.description,
            "ip_address": t.ip_address,
            "device_id": t.device_id,
            "payment_record": payment_data,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        },
    }


# ─── Payment Execution Router ─────────────────────────────────
@payments_router.post("/transfer")
def initiate_payment_transfer(
    req: TransferRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ip_addr = request.client.host if request.client else "127.0.0.1"

    # Step 1: Pre-transfer Sanctions Screening on recipient name if provided
    if req.recipient_name:
        matches = SanctionsScreeningService.screen_entity(
            db=db,
            query_name=req.recipient_name,
            threshold=85.0,
        )
        if any(m.match_score >= 95.0 for m in matches):
            raise HTTPException(
                status_code=403,
                detail=f"Payment blocked by Sanctions Compliance: Recipient '{req.recipient_name}' matched critical watchlist entry.",
            )

    # Step 2: Atomic Execution via BankingService
    try:
        txn, exec_res = BankingService.execute_transfer(
            db=db,
            source_account_id=req.source_account_id,
            destination_account_id=req.destination_account_id,
            amount=req.amount,
            payment_rail=req.payment_rail,
            idempotency_key=req.idempotency_key,
            recipient_identifier=req.recipient_identifier,
            recipient_name=req.recipient_name,
            description=req.description,
            ip_address=ip_addr,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 3: Post-transfer Automated AML Screening
    if txn.status == "COMPLETED" and txn.source_account and txn.source_account.customer_id:
        AMLMonitoringService.evaluate_transaction(
            db=db,
            customer_id=txn.source_account.customer_id,
            transaction=txn,
        )

    return {
        "success": exec_res.success,
        "data": {
            "transaction_id": txn.id,
            "transaction_reference": txn.transaction_reference,
            "status": txn.status,
            "amount": txn.amount,
            "currency": txn.currency,
            "fee_applied": txn.fee_amount,
            "payment_rail": txn.payment_rail,
            "provider_name": exec_res.provider_name,
            "provider_reference": exec_res.provider_reference,
            "is_sandbox": exec_res.is_sandbox,
            "clearing_time_ms": round(exec_res.clearing_time_ms, 2),
            "error_message": exec_res.error_message,
        },
    }


@payments_router.post("/upi/create-intent")
def create_upi_intent(
    req: UPIIntentCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    intent_ref = f"UPI-INT-{uuid.uuid4().hex[:8].upper()}"
    qr_payload = f"upi://pay?pa={req.payee_vpa}&pn={req.payee_name.replace(' ', '%20')}&am={req.amount:.2f}&cu={req.currency}&tn={req.note.replace(' ', '%20')}&tr={intent_ref}"
    expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

    intent = UPIPaymentIntent(
        intent_reference=intent_ref,
        payee_vpa=req.payee_vpa,
        payee_name=req.payee_name,
        amount=req.amount,
        currency=req.currency,
        note=req.note,
        qr_payload=qr_payload,
        status="ACTIVE",
        expires_at=expiry,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)

    return {
        "success": True,
        "data": {
            "intent_reference": intent.intent_reference,
            "payee_vpa": intent.payee_vpa,
            "payee_name": intent.payee_name,
            "amount": intent.amount,
            "currency": intent.currency,
            "qr_payload": intent.qr_payload,
            "status": intent.status,
            "expires_at": intent.expires_at.isoformat(),
        },
    }
