"""Loan and EMI Calculation Service with Full Amortization Schedules."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.customer import Customer
from app.models.loan import Loan, LoanPayment


class LoanService:
    """Financial Amortization, EMI Formulas, and Loan Portfolio Lifecycle."""

    @staticmethod
    def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> Tuple[float, float, float]:
        """Calculate Equated Monthly Installment (EMI), Total Interest, and Total Payable.
        
        Formula: E = P * r * (1+r)^n / ((1+r)^n - 1)
        """
        if principal <= 0 or tenure_months <= 0:
            return 0.0, 0.0, 0.0

        monthly_r = (annual_rate_pct / 100.0) / 12.0
        if monthly_r == 0:
            emi = principal / tenure_months
        else:
            pow_factor = math.pow(1 + monthly_r, tenure_months)
            emi = principal * monthly_r * pow_factor / (pow_factor - 1)

        emi = round(emi, 2)
        total_payable = round(emi * tenure_months, 2)
        total_interest = round(total_payable - principal, 2)

        return emi, total_interest, total_payable

    @staticmethod
    def generate_amortization_schedule(
        principal: float, annual_rate_pct: float, tenure_months: int, start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Generate monthly breakdown of principal, interest, and remaining balance."""
        start_t = start_date or datetime.now(timezone.utc)
        emi, _, _ = LoanService.calculate_emi(principal, annual_rate_pct, tenure_months)
        monthly_r = (annual_rate_pct / 100.0) / 12.0

        schedule = []
        remaining = principal

        for i in range(1, tenure_months + 1):
            interest_comp = round(remaining * monthly_r, 2)
            principal_comp = round(emi - interest_comp, 2)
            
            # Final month adjustment
            if i == tenure_months:
                principal_comp = remaining
                emi_actual = round(principal_comp + interest_comp, 2)
                remaining = 0.0
            else:
                remaining = round(max(0.0, remaining - principal_comp), 2)
                emi_actual = emi

            due_date = start_t + timedelta(days=30 * i)
            schedule.append({
                "installment_number": i,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "emi_amount": emi_actual,
                "principal_component": principal_comp,
                "interest_component": interest_comp,
                "remaining_balance": remaining,
                "status": "SCHEDULED",
            })

        return schedule

    @staticmethod
    def originate_loan(
        db: Session,
        customer_id: str,
        bank_id: str,
        loan_type: str,
        principal_amount: float,
        interest_rate_annual: float,
        tenure_months: int,
        account_id: Optional[str] = None,
    ) -> Loan:
        """Create and disburse new loan, generating linked amortization schedule."""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        emi, total_interest, total_payable = LoanService.calculate_emi(
            principal_amount, interest_rate_annual, tenure_months
        )

        loan_number = f"LN-{loan_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
        start_date = datetime.now(timezone.utc)
        maturity_date = start_date + timedelta(days=30 * tenure_months)

        loan = Loan(
            customer_id=customer_id,
            bank_id=bank_id,
            account_id=account_id,
            loan_number=loan_number,
            loan_type=loan_type.upper(),
            currency="INR",
            principal_amount=principal_amount,
            interest_rate_annual=interest_rate_annual,
            tenure_months=tenure_months,
            emi_amount=emi,
            total_interest_payable=total_interest,
            total_amount_payable=total_payable,
            outstanding_principal=principal_amount,
            paid_principal=0.0,
            paid_interest=0.0,
            status="ACTIVE",
            risk_grade="A" if customer.credit_score >= 750 else "BBB" if customer.credit_score >= 650 else "C",
            start_date=start_date,
            next_due_date=start_date + timedelta(days=30),
            maturity_date=maturity_date,
            disbursed_at=start_date,
        )
        db.add(loan)
        db.flush()

        # Build schedule entries
        schedule = LoanService.generate_amortization_schedule(
            principal_amount, interest_rate_annual, tenure_months, start_date
        )
        for row in schedule:
            payment_entry = LoanPayment(
                loan_id=loan.id,
                installment_number=row["installment_number"],
                due_date=datetime.strptime(row["due_date"], "%Y-%m-%d"),
                emi_amount=row["emi_amount"],
                principal_component=row["principal_component"],
                interest_component=row["interest_component"],
                remaining_balance=row["remaining_balance"],
                status="SCHEDULED",
            )
            db.add(payment_entry)

        db.commit()
        db.refresh(loan)
        return loan
