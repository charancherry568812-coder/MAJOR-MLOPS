"""Anti-Money Laundering (AML) Transaction Monitoring and Case Management Engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction_payment import Transaction
from app.models.kyc_aml_sanctions import AMLAlert, AMLCase


class AMLMonitoringService:
    """Automated AML Risk Rule Engine & SAR Workflow."""

    # Statutory Thresholds (configurable)
    STRUCTURING_RANGE_MIN = 45000.0   # Just below ₹50,000 PAN threshold
    STRUCTURING_RANGE_MAX = 49999.0
    HIGH_RISK_COUNTRIES = ["IR", "KP", "SY", "CU", "MM"]

    @staticmethod
    def evaluate_transaction(
        db: Session,
        customer_id: str,
        transaction: Transaction,
        destination_country: str = "IN",
    ) -> List[AMLAlert]:
        """Inspect transaction against all regulatory AML rules."""
        generated_alerts: List[AMLAlert] = []
        customer = db.query(Customer).filter(Customer.id == customer_id).first()

        # 1. Structuring / Smurfing Rule Check: Multiple transactions just below cash/tax thresholds
        if AMLMonitoringService.STRUCTURING_RANGE_MIN <= transaction.amount <= AMLMonitoringService.STRUCTURING_RANGE_MAX:
            alert = AMLAlert(
                alert_code=f"AML-STRUC-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer_id,
                transaction_id=transaction.id,
                alert_type="STRUCTURING",
                severity="HIGH",
                risk_score=82.0,
                status="OPEN",
                resolution_notes="Transaction amount ₹{:.2f} is just below the ₹50,000 regulatory reporting threshold.".format(transaction.amount),
            )
            generated_alerts.append(alert)

        # 2. Velocity Anomaly Rule: > 5 transactions in the last 10 minutes
        ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        recent_tx_count = db.query(Transaction).filter(
            Transaction.source_account_id.in_(
                db.query(Account.id).filter(Account.customer_id == customer_id)
            ),
            Transaction.created_at >= ten_mins_ago,
        ).count()

        if recent_tx_count >= 5:
            alert = AMLAlert(
                alert_code=f"AML-VELO-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer_id,
                transaction_id=transaction.id,
                alert_type="VELOCITY_ANOMALY",
                severity="HIGH",
                risk_score=78.5,
                status="OPEN",
                resolution_notes=f"Rapid velocity: {recent_tx_count} transactions recorded within 10 minutes.",
            )
            generated_alerts.append(alert)

        # 3. High-Risk Geography Rule
        if destination_country.upper() in AMLMonitoringService.HIGH_RISK_COUNTRIES:
            alert = AMLAlert(
                alert_code=f"AML-GEO-{uuid.uuid4().hex[:6].upper()}",
                customer_id=customer_id,
                transaction_id=transaction.id,
                alert_type="HIGH_RISK_GEO",
                severity="CRITICAL",
                risk_score=95.0,
                status="OPEN",
                resolution_notes=f"Transaction routed to high-risk FATF monitored jurisdiction ({destination_country.upper()}).",
            )
            generated_alerts.append(alert)

        # 4. Sudden Spike / Rapid Movement of Funds: Transaction > 5x customer's typical balance
        if customer and customer.accounts:
            avg_balance = sum(a.balance for a in customer.accounts) / len(customer.accounts)
            if avg_balance > 0 and transaction.amount > (avg_balance * 5.0) and transaction.amount > 200000.0:
                alert = AMLAlert(
                    alert_code=f"AML-SPIKE-{uuid.uuid4().hex[:6].upper()}",
                    customer_id=customer_id,
                    transaction_id=transaction.id,
                    alert_type="RAPID_MOVEMENT",
                    severity="MEDIUM",
                    risk_score=68.0,
                    status="OPEN",
                    resolution_notes="Sudden high-value spike: Transfer exceeds 5x customer average balance history.",
                )
                generated_alerts.append(alert)

        # Persist alerts to DB if triggered
        if generated_alerts:
            for al in generated_alerts:
                db.add(al)
            db.commit()

        return generated_alerts

    @staticmethod
    def resolve_alert(
        db: Session,
        alert_id: str,
        resolution: str,  # RESOLVED, FALSE_POSITIVE, ESCALATED
        notes: str,
        reviewer_id: str,
    ) -> AMLAlert:
        """Resolve AML alert or escalate to full investigation case."""
        alert = db.query(AMLAlert).filter(AMLAlert.id == alert_id).first()
        if not alert:
            raise ValueError(f"AML Alert {alert_id} not found")

        alert.status = resolution.upper()
        alert.assigned_to = reviewer_id
        alert.resolution_notes = notes
        alert.updated_at = datetime.now(timezone.utc)

        if resolution.upper() == "ESCALATED":
            case = AMLCase(
                case_number=f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                title=f"Escalated AML Investigation: {alert.alert_type}",
                customer_id=alert.customer_id,
                primary_alert_id=alert.id,
                priority="HIGH",
                status="UNDER_REVIEW",
                findings_summary=notes,
                created_by=reviewer_id,
            )
            db.add(case)

        db.commit()
        db.refresh(alert)
        return alert
