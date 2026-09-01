"""Loan Portfolio, EMI Calculation, and Repayments API Router."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.loan import Loan, LoanPayment
from app.schemas.banking import EMICalculateRequest, EMICalculateResponse, LoanApplyRequest
from app.services.loan_service import LoanService

loans_router = APIRouter(prefix="/loans", tags=["Loans & Credit"])


@loans_router.get("")
def list_loans(
    customer_id: Optional[str] = None,
    loan_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Loan)
    if customer_id:
        query = query.filter(Loan.customer_id == customer_id)
    if loan_type:
        query = query.filter(Loan.loan_type == loan_type.upper())
    if status:
        query = query.filter(Loan.status == status.upper())

    total = query.count()
    loans = query.order_by(Loan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for l in loans:
        items.append({
            "id": l.id,
            "loan_number": l.loan_number,
            "customer_id": l.customer_id,
            "customer_name": f"{l.customer.first_name} {l.customer.last_name}" if l.customer else "",
            "loan_type": l.loan_type,
            "principal_amount": l.principal_amount,
            "interest_rate_annual": l.interest_rate_annual,
            "tenure_months": l.tenure_months,
            "emi_amount": l.emi_amount,
            "outstanding_principal": l.outstanding_principal,
            "risk_grade": l.risk_grade,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@loans_router.get("/{loan_id}")
def get_loan_detail(loan_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    l = db.query(Loan).filter(Loan.id == loan_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Loan not found")

    payments_data = [{
        "id": p.id,
        "installment_number": p.installment_number,
        "due_date": p.due_date.strftime("%Y-%m-%d") if p.due_date else "",
        "emi_amount": p.emi_amount,
        "principal_component": p.principal_component,
        "interest_component": p.interest_component,
        "remaining_balance": p.remaining_balance,
        "status": p.status,
    } for p in l.payments]

    return {
        "success": True,
        "data": {
            "id": l.id,
            "loan_number": l.loan_number,
            "customer_id": l.customer_id,
            "customer_name": f"{l.customer.first_name} {l.customer.last_name}" if l.customer else "",
            "loan_type": l.loan_type,
            "currency": l.currency,
            "principal_amount": l.principal_amount,
            "interest_rate_annual": l.interest_rate_annual,
            "tenure_months": l.tenure_months,
            "emi_amount": l.emi_amount,
            "total_interest_payable": l.total_interest_payable,
            "total_amount_payable": l.total_amount_payable,
            "outstanding_principal": l.outstanding_principal,
            "paid_principal": l.paid_principal,
            "paid_interest": l.paid_interest,
            "status": l.status,
            "risk_grade": l.risk_grade,
            "start_date": l.start_date.isoformat() if l.start_date else None,
            "maturity_date": l.maturity_date.isoformat() if l.maturity_date else None,
            "amortization_schedule": payments_data,
        },
    }


@loans_router.post("/calculate-emi")
def calculate_emi_endpoint(req: EMICalculateRequest):
    emi, total_interest, total_payable = LoanService.calculate_emi(
        req.principal_amount, req.interest_rate_annual, req.tenure_months
    )
    schedule = LoanService.generate_amortization_schedule(
        req.principal_amount, req.interest_rate_annual, req.tenure_months
    )

    return {
        "success": True,
        "data": EMICalculateResponse(
            principal_amount=req.principal_amount,
            interest_rate_annual=req.interest_rate_annual,
            tenure_months=req.tenure_months,
            monthly_emi=emi,
            total_interest=total_interest,
            total_payable=total_payable,
            amortization_preview=schedule[:12],  # First 12 months preview
        ).model_dump(),
    }


@loans_router.post("/apply")
def apply_for_loan(
    req: LoanApplyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "DATA_SCIENTIST", "SUPER_ADMIN"])),
):
    try:
        loan = LoanService.originate_loan(
            db=db,
            customer_id=req.customer_id,
            bank_id=req.bank_id,
            loan_type=req.loan_type,
            principal_amount=req.principal_amount,
            interest_rate_annual=req.interest_rate_annual,
            tenure_months=req.tenure_months,
            account_id=req.account_id,
        )
        return {
            "success": True,
            "data": {
                "id": loan.id,
                "loan_number": loan.loan_number,
                "emi_amount": loan.emi_amount,
                "status": loan.status,
                "risk_grade": loan.risk_grade,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
