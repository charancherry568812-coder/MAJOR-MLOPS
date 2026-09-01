"""Customer Management API Router."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.customer import Customer, CustomerProfile
from app.models.bank import Bank
from app.schemas.banking import CustomerCreateRequest, CustomerResponse

customers_router = APIRouter(prefix="/customers", tags=["Customers"])


@customers_router.get("")
def list_customers(
    bank_id: Optional[str] = None,
    segment: Optional[str] = None,
    kyc_status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Customer)
    if bank_id:
        query = query.filter(Customer.bank_id == bank_id)
    if segment:
        query = query.filter(Customer.customer_segment == segment.upper())
    if kyc_status:
        query = query.filter(Customer.kyc_status == kyc_status.upper())
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Customer.first_name.ilike(term)) |
            (Customer.last_name.ilike(term)) |
            (Customer.email.ilike(term)) |
            (Customer.customer_number.ilike(term)) |
            (Customer.phone.ilike(term))
        )

    total = query.count()
    items = query.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [CustomerResponse.model_validate(c).model_dump() for c in items],
        },
    }


@customers_router.get("/{customer_id}")
def get_customer_detail(customer_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")

    accounts_data = [{
        "id": a.id, "account_number": a.account_number, "account_type": a.account_type,
        "currency": a.currency, "balance": a.balance, "available_balance": a.available_balance,
        "status": a.status, "upi_vpa": a.upi_vpa,
    } for a in c.accounts]

    loans_data = [{
        "id": l.id, "loan_number": l.loan_number, "loan_type": l.loan_type,
        "principal_amount": l.principal_amount, "emi_amount": l.emi_amount,
        "outstanding_principal": l.outstanding_principal, "status": l.status,
    } for l in c.loans]

    cards_data = [{
        "id": cd.id, "card_number_masked": cd.card_number_masked, "card_type": cd.card_type,
        "card_network": cd.card_network, "status": cd.status,
    } for cd in c.cards]

    return {
        "success": True,
        "data": {
            **CustomerResponse.model_validate(c).model_dump(),
            "accounts": accounts_data,
            "loans": loans_data,
            "cards": cards_data,
            "kyc_cases_count": len(c.kyc_cases),
            "aml_alerts_count": len(c.aml_alerts),
        },
    }


@customers_router.post("")
def create_customer(
    req: CustomerCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "DATA_SCIENTIST", "SUPER_ADMIN"])),
):
    bank = db.query(Bank).filter(Bank.id == req.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    cust_num = f"CUST-{bank.code[:4]}-{uuid.uuid4().hex[:6].upper()}"
    customer = Customer(
        bank_id=req.bank_id,
        customer_number=cust_num,
        customer_type=req.customer_type.upper(),
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        phone=req.phone,
        date_of_birth=req.date_of_birth,
        country_code=req.country_code.upper(),
        address_line1=req.address_line1,
        city=req.city,
        state=req.state,
        postal_code=req.postal_code,
        employment_status=req.employment_status,
        annual_income=req.annual_income,
        pan_number=req.pan_number.upper() if req.pan_number else None,
        credit_score=750,
        credit_risk_tier="LOW_RISK",
        customer_segment="RETAIL",
        kyc_status="VERIFIED" if req.pan_number else "PENDING",
        aml_status="CLEAR",
        account_status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {"success": True, "data": CustomerResponse.model_validate(customer).model_dump()}
