"""Account Management & Statements API Router."""

from __future__ import annotations

import csv
import io
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.account import Account, Beneficiary
from app.models.customer import Customer
from app.models.transaction_payment import Transaction
from app.schemas.banking import AccountCreateRequest, AccountResponse, BeneficiaryCreateRequest
from app.services.banking_service import BankingService

accounts_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@accounts_router.get("")
def list_accounts(
    customer_id: Optional[str] = None,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Account)
    if customer_id:
        query = query.filter(Account.customer_id == customer_id)
    if account_type:
        query = query.filter(Account.account_type == account_type.upper())
    if status:
        query = query.filter(Account.status == status.upper())

    total = query.count()
    items = query.order_by(Account.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [AccountResponse.model_validate(a).model_dump() for a in items],
        },
    }


@accounts_router.get("/{account_id}")
def get_account_detail(account_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    customer_info = {
        "customer_id": acc.customer.id if acc.customer else "",
        "customer_name": f"{acc.customer.first_name} {acc.customer.last_name}" if acc.customer else "",
        "email": acc.customer.email if acc.customer else "",
        "phone": acc.customer.phone if acc.customer else "",
    }

    return {
        "success": True,
        "data": {
            **AccountResponse.model_validate(acc).model_dump(),
            "customer": customer_info,
            "bank_name": acc.bank.name if acc.bank else "",
            "branch_name": acc.branch.name if acc.branch else "Main Branch",
            "ifsc_code": acc.branch.ifsc_code if acc.branch else "FEDB0001001",
        },
    }


@accounts_router.post("")
def open_account(
    req: AccountCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "DATA_SCIENTIST", "SUPER_ADMIN"])),
):
    try:
        acc = BankingService.create_account(
            db=db,
            customer_id=req.customer_id,
            bank_id=req.bank_id,
            account_type=req.account_type,
            currency=req.currency,
            initial_deposit=req.initial_deposit,
            branch_id=req.branch_id,
        )
        return {"success": True, "data": AccountResponse.model_validate(acc).model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@accounts_router.post("/{account_id}/toggle-freeze")
def toggle_account_freeze(
    account_id: str,
    reason: Optional[str] = "Administrative Review",
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "SUPER_ADMIN"])),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    if acc.status == "ACTIVE":
        acc.status = "FROZEN"
        acc.freeze_reason = reason
    else:
        acc.status = "ACTIVE"
        acc.freeze_reason = None

    db.commit()
    return {"success": True, "data": {"id": acc.id, "status": acc.status, "reason": acc.freeze_reason}}


@accounts_router.get("/{account_id}/transactions")
def get_account_transactions(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    query = db.query(Transaction).filter(
        (Transaction.source_account_id == account_id) | (Transaction.destination_account_id == account_id)
    ).order_by(Transaction.created_at.desc())

    total = query.count()
    txns = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for t in txns:
        is_debit = t.source_account_id == account_id
        items.append({
            "id": t.id,
            "reference": t.transaction_reference,
            "type": "DEBIT" if is_debit else "CREDIT",
            "amount": t.amount,
            "currency": t.currency,
            "rail": t.payment_rail,
            "status": t.status,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@accounts_router.get("/{account_id}/statement")
def download_statement_csv(
    account_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    txns = db.query(Transaction).filter(
        (Transaction.source_account_id == account_id) | (Transaction.destination_account_id == account_id)
    ).order_by(Transaction.created_at.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Transaction Ref", "Type", "Amount", "Currency", "Payment Rail", "Status", "Description"])

    for t in txns:
        is_debit = t.source_account_id == account_id
        writer.writerow([
            t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
            t.transaction_reference,
            "DEBIT" if is_debit else "CREDIT",
            f"-{t.amount:.2f}" if is_debit else f"+{t.amount:.2f}",
            t.currency,
            t.payment_rail,
            t.status,
            t.description,
        ])

    csv_data = output.getvalue()
    filename = f"statement_{acc.account_number}_{acc.currency}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── Beneficiaries ───────────────────────────────────────────
@accounts_router.get("/{account_id}/beneficiaries")
def list_beneficiaries(account_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    b_list = db.query(Beneficiary).filter(Beneficiary.customer_id == acc.customer_id).all()
    return {"success": True, "data": [{
        "id": b.id, "nickname": b.nickname, "beneficiary_name": b.beneficiary_name,
        "account_number": b.account_number, "ifsc_code": b.ifsc_code,
        "upi_vpa": b.upi_vpa, "iban": b.iban, "payment_rail": b.payment_rail,
        "currency": b.currency, "transfer_limit": b.transfer_limit,
    } for b in b_list]}


@accounts_router.post("/{account_id}/beneficiaries")
def add_beneficiary(
    account_id: str,
    req: BeneficiaryCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    ben = Beneficiary(
        customer_id=acc.customer_id,
        nickname=req.nickname,
        beneficiary_name=req.beneficiary_name,
        account_number=req.account_number,
        ifsc_code=req.ifsc_code,
        upi_vpa=req.upi_vpa,
        iban=req.iban,
        swift_bic=req.swift_bic,
        bank_name=req.bank_name,
        country_code=req.country_code,
        currency=req.currency,
        payment_rail=req.payment_rail.upper(),
        transfer_limit=req.transfer_limit,
        is_verified=True,
    )
    db.add(ben)
    db.commit()
    db.refresh(ben)

    return {"success": True, "data": {"id": ben.id, "nickname": ben.nickname, "status": "VERIFIED"}}
