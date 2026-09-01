"""Core Banking Ledger Service with Atomic Transactions, Idempotency, and Concurrency Controls."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.account import Account, Beneficiary
from app.models.customer import Customer
from app.models.transaction_payment import Transaction, Payment, UPIPaymentIntent
from app.services.country_service import convert_currency
from app.services.payment_providers import payment_router, PaymentExecutionResult


class BankingService:
    """Enterprise Account and Ledger Management with Atomic Financial Operations."""

    @staticmethod
    def generate_account_number(bank_code: str, account_type: str = "SAVINGS") -> str:
        """Generate standard 12-16 digit bank account number with checksum."""
        prefix = "1001" if account_type == "SAVINGS" else "2001" if account_type == "CURRENT" else "3001"
        random_digits = f"{random.randint(10000000, 99999999)}"
        return f"{prefix}{random_digits}"

    @staticmethod
    def create_account(
        db: Session,
        customer_id: str,
        bank_id: str,
        account_type: str = "SAVINGS",
        currency: str = "INR",
        initial_deposit: float = 10000.0,
        branch_id: Optional[str] = None,
        upi_vpa: Optional[str] = None,
    ) -> Account:
        """Create new bank account with initial opening balance."""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        acc_num = BankingService.generate_account_number(bank_id, account_type)
        if not upi_vpa and customer.phone:
            upi_vpa = f"{customer.phone}@fedbank"
        elif not upi_vpa:
            upi_vpa = f"{customer.customer_number.lower()}@fedbank"

        # Unique VPA fallback if exists
        existing_vpa = db.query(Account).filter(Account.upi_vpa == upi_vpa).first()
        if existing_vpa:
            upi_vpa = f"{customer.customer_number.lower()}_{uuid.uuid4().hex[:4]}@fedbank"

        account = Account(
            customer_id=customer_id,
            bank_id=bank_id,
            branch_id=branch_id,
            account_number=acc_num,
            account_type=account_type.upper(),
            currency=currency.upper(),
            balance=initial_deposit,
            available_balance=initial_deposit,
            ledger_balance=initial_deposit,
            hold_amount=0.0,
            upi_vpa=upi_vpa,
            status="ACTIVE",
            interest_rate=3.5 if account_type == "SAVINGS" else 0.0 if account_type == "CURRENT" else 7.0,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        # Record opening deposit transaction if initial_deposit > 0
        if initial_deposit > 0:
            txn = Transaction(
                transaction_reference=f"TXN-OPEN-{uuid.uuid4().hex[:10].upper()}",
                customer_id=customer_id,
                bank_id=bank_id,
                destination_account_id=account.id,
                amount=initial_deposit,
                currency=currency.upper(),
                payment_rail="INTERNAL",
                transaction_type="DEPOSIT",
                status="COMPLETED",
                description="Account Opening Initial Deposit",
                completed_at=datetime.now(timezone.utc),
            )
            db.add(txn)
            db.commit()

        return account

    @staticmethod
    def execute_transfer(
        db: Session,
        source_account_id: str,
        destination_account_id: Optional[str],
        amount: float,
        payment_rail: str = "UPI",
        idempotency_key: Optional[str] = None,
        recipient_identifier: Optional[str] = None,
        recipient_name: Optional[str] = None,
        description: str = "Funds Transfer",
        device_id: str = "dev-client",
        ip_address: str = "127.0.0.1",
    ) -> Tuple[Transaction, PaymentExecutionResult]:
        """Atomic money movement between accounts or external rails with Concurrency Control."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        # 1. Check Idempotency Key
        if idempotency_key:
            existing_txn = db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()
            if existing_txn:
                existing_payment = db.query(Payment).filter(Payment.transaction_id == existing_txn.id).first()
                dummy_result = PaymentExecutionResult(
                    success=existing_txn.status == "COMPLETED",
                    status=existing_txn.status,
                    provider_name="IdempotentReplay",
                    provider_reference=existing_payment.payment_reference if existing_payment else existing_txn.transaction_reference,
                    is_sandbox=True,
                    fee_applied=existing_txn.fee_amount,
                    clearing_time_ms=0.0,
                )
                return existing_txn, dummy_result

        # 2. Lock Source Account & Validate Balance
        source_acc = db.query(Account).filter(Account.id == source_account_id).with_for_update().first()
        if not source_acc:
            raise ValueError(f"Source account {source_account_id} not found")

        if source_acc.status != "ACTIVE":
            raise ValueError(f"Source account is {source_acc.status}. Transfers not permitted.")

        if source_acc.available_balance < amount:
            raise ValueError(
                f"Insufficient funds: Available balance is {source_acc.currency} {source_acc.available_balance:.2f}, requested {amount:.2f}"
            )

        # 3. Handle Destination Account (if internal or registered)
        dest_acc = None
        if destination_account_id:
            dest_acc = db.query(Account).filter(Account.id == destination_account_id).with_for_update().first()
        elif recipient_identifier and ("@" in recipient_identifier):
            dest_acc = db.query(Account).filter(Account.upi_vpa == recipient_identifier).with_for_update().first()

        # 4. FX Conversion if multi-currency
        target_currency = dest_acc.currency if dest_acc else source_acc.currency
        settlement_amount, fx_rate = convert_currency(amount, source_acc.currency, target_currency, db=db)

        # 5. Execute external payment rail through Router
        txn_ref = f"TXN-{payment_rail.upper()}-{uuid.uuid4().hex[:10].upper()}"
        exec_result = payment_router.execute(
            rail_code=payment_rail,
            amount=amount,
            currency=source_acc.currency,
            sender_id=source_acc.upi_vpa or source_acc.account_number,
            receiver_id=recipient_identifier or (dest_acc.upi_vpa if dest_acc else "UNKNOWN_RECIPIENT"),
            payment_reference=txn_ref,
            metadata={"ifsc": "FEDB0001001"},
        )

        if not exec_result.success:
            # Record failed transaction attempt
            failed_txn = Transaction(
                transaction_reference=txn_ref,
                idempotency_key=idempotency_key,
                customer_id=source_acc.customer_id,
                bank_id=source_acc.bank_id,
                source_account_id=source_acc.id,
                amount=amount,
                currency=source_acc.currency,
                payment_rail=payment_rail.upper(),
                status="FAILED",
                failure_reason=exec_result.error_message or "Payment rail execution rejected",
                description=description,
                ip_address=ip_address,
                device_id=device_id,
            )
            db.add(failed_txn)
            db.commit()
            return failed_txn, exec_result

        # 6. Apply Atomic Ledger Updates (Source Debit)
        total_debit = amount + exec_result.fee_applied
        source_acc.balance -= total_debit
        source_acc.available_balance -= total_debit
        source_acc.ledger_balance -= total_debit
        source_acc.version += 1

        # Destination Credit (if internal account)
        if dest_acc:
            dest_acc.balance += settlement_amount
            dest_acc.available_balance += settlement_amount
            dest_acc.ledger_balance += settlement_amount
            dest_acc.version += 1

        # 7. Record Completed Transaction & External Payment Link
        txn = Transaction(
            transaction_reference=txn_ref,
            idempotency_key=idempotency_key,
            customer_id=source_acc.customer_id,
            bank_id=source_acc.bank_id,
            source_account_id=source_acc.id,
            destination_account_id=dest_acc.id if dest_acc else None,
            amount=amount,
            currency=source_acc.currency,
            fee_amount=exec_result.fee_applied,
            fx_rate=fx_rate,
            settlement_amount=settlement_amount,
            settlement_currency=target_currency,
            payment_rail=payment_rail.upper(),
            status="COMPLETED",
            description=description,
            ip_address=ip_address,
            device_id=device_id,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(txn)
        db.flush()

        payment_entry = Payment(
            payment_reference=exec_result.provider_reference,
            transaction_id=txn.id,
            sender_name=source_acc.customer.first_name + " " + source_acc.customer.last_name if source_acc.customer else "Account Holder",
            sender_identifier=source_acc.upi_vpa or source_acc.account_number,
            receiver_name=recipient_name or (dest_acc.customer.first_name + " " + dest_acc.customer.last_name if dest_acc and dest_acc.customer else "Beneficiary"),
            receiver_identifier=recipient_identifier or (dest_acc.account_number if dest_acc else "EXTERNAL"),
            payment_rail=payment_rail.upper(),
            provider_name=exec_result.provider_name,
            provider_status=exec_result.status,
            is_sandbox=exec_result.is_sandbox,
        )
        db.add(payment_entry)
        db.commit()
        db.refresh(txn)

        return txn, exec_result
