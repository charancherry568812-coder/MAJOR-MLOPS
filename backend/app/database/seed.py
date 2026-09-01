"""Seed the database with enterprise banking entities, countries, currencies, rails, customers, accounts, loans, cards, compliance cases, ML models, and audit trails."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import Role, User
from app.models.banking_country import Country, Currency, BankingRegulation, PaymentRailConfig
from app.models.bank import Bank, BankUser
from app.models.branch import Branch
from app.models.customer import Customer, CustomerProfile
from app.models.account import Account, Beneficiary
from app.models.transaction_payment import Transaction, Payment, UPIPaymentIntent
from app.models.loan import Loan, LoanPayment
from app.models.card import Card
from app.models.kyc_aml_sanctions import KYCCase, KYCDocument, AMLAlert, AMLCase, SanctionsWatchlist
from app.models.client import FederatedClient
from app.models.settings import SystemSetting
from app.models.fraud import FraudAlert
from app.models.ml_model import MLModel, ModelVersion
from app.models.drift_quality import AdvancedDataDriftReport, ModelDriftReport
from app.models.audit import AuditLog
from app.services.country_service import COUNTRY_DEFINITIONS, CURRENCY_METADATA, INITIAL_FX_RATES
from app.services.loan_service import LoanService

logger = logging.getLogger(__name__)

ROLES = [
    {"name": "SUPER_ADMIN", "description": "System administrator with full enterprise access"},
    {"name": "ADMIN", "description": "System administrator (alias for SUPER_ADMIN)"},
    {"name": "BANK_ADMIN", "description": "Bank-level administrator with local data control"},
    {"name": "ML_ENGINEER", "description": "Machine learning engineer with model & pipeline control"},
    {"name": "DATA_SCIENTIST", "description": "Data scientist with experiment & dataset access"},
    {"name": "AUDITOR", "description": "Auditor with compliance & audit log review access"},
    {"name": "VIEWER", "description": "Read-only viewer with dashboard inspection access"},
    {"name": "CUSTOMER", "description": "Retail / corporate banking customer access"},
]

BANKS = [
    {
        "name": "Alpha National Bank",
        "code": "BANK-001",
        "branch": "Nariman Point Financial Tower",
        "contact_person": "Aditya Sharma",
        "email": "contact@alphanational.com",
        "phone": "+91-22-6611-0101",
        "location": "Mumbai, Maharashtra, India",
        "country_code": "IN",
        "num_customers": 5000,
        "dataset_size": 5000,
        "current_model_version": "v2.1.0",
        "accuracy": 0.892,
        "participation_status": "ACTIVE",
    },
    {
        "name": "Beta Federal Bank",
        "code": "BANK-002",
        "branch": "Connaught Place Regional Hub",
        "contact_person": "Bhavna Patel",
        "email": "contact@betafederal.com",
        "phone": "+91-11-4422-0102",
        "location": "New Delhi, Delhi, India",
        "country_code": "IN",
        "num_customers": 4500,
        "dataset_size": 4500,
        "current_model_version": "v2.1.0",
        "accuracy": 0.874,
        "participation_status": "ACTIVE",
    },
    {
        "name": "Gamma Trust Bank",
        "code": "BANK-003",
        "branch": "Whitefield Tech Park Branch",
        "contact_person": "Chetan Rao",
        "email": "contact@gammatrust.com",
        "phone": "+91-80-2233-0103",
        "location": "Bengaluru, Karnataka, India",
        "country_code": "IN",
        "num_customers": 6000,
        "dataset_size": 6000,
        "current_model_version": "v2.1.0",
        "accuracy": 0.865,
        "participation_status": "ACTIVE",
    },
    {
        "name": "Delta Savings Bank",
        "code": "BANK-004",
        "branch": "HITEC City Innovation Hub",
        "contact_person": "Deepa Reddy",
        "email": "contact@deltasavings.com",
        "phone": "+91-40-7788-0104",
        "location": "Hyderabad, Telangana, India",
        "country_code": "IN",
        "num_customers": 5500,
        "dataset_size": 5500,
        "current_model_version": "v2.1.0",
        "accuracy": 0.881,
        "participation_status": "ACTIVE",
    },
]

DEFAULT_SETTINGS = [
    {"key": "min_model_accuracy", "value": "0.75", "description": "Minimum model accuracy required for production deployment", "category": "model"},
    {"key": "min_model_f1", "value": "0.70", "description": "Minimum F1 score for production approval", "category": "model"},
    {"key": "min_model_auc", "value": "0.75", "description": "Minimum ROC-AUC for production approval", "category": "model"},
    {"key": "data_drift_threshold", "value": "0.20", "description": "Population Stability Index (PSI) threshold for data drift alerts", "category": "monitoring"},
    {"key": "model_drift_threshold", "value": "0.08", "description": "Performance degradation threshold for model retraining alert", "category": "monitoring"},
    {"key": "high_risk_threshold", "value": "0.70", "description": "Probability threshold classifying applicant as HIGH RISK", "category": "prediction"},
    {"key": "medium_risk_threshold", "value": "0.40", "description": "Probability threshold classifying applicant as MEDIUM RISK", "category": "prediction"},
    {"key": "fraud_score_threshold", "value": "0.65", "description": "Threshold for automatically flagging transactions as suspicious", "category": "fraud"},
    {"key": "api_alert_threshold", "value": "3.0", "description": "API latency threshold (seconds) for performance warning", "category": "system"},
]


def seed_database(db: Session) -> None:
    """Seed full enterprise banking platform with referential integrity."""
    logger.info("Checking database seed state...")

    # 1. Seed Countries
    for c in COUNTRY_DEFINITIONS:
        if not db.query(Country).filter(Country.code == c["code"]).first():
            db.add(Country(
                code=c["code"],
                code_alpha3=c["code_alpha3"],
                name=c["name"],
                default_currency=c["default_currency"],
                locale=c["locale"],
                timezone=c["timezone"],
                regulatory_body=c["regulatory_body"],
            ))
    db.commit()

    # 2. Seed Currencies
    for cur in CURRENCY_METADATA:
        if not db.query(Currency).filter(Currency.code == cur["code"]).first():
            db.add(Currency(
                code=cur["code"],
                name=cur["name"],
                symbol=cur["symbol"],
                decimals=cur["decimals"],
                exchange_rate_to_usd=INITIAL_FX_RATES.get(cur["code"], 1.0),
                is_base=cur["is_base"],
            ))
    db.commit()

    # 3. Seed Payment Rails
    default_rails = [
        {"rail_code": "UPI", "rail_name": "Unified Payments Interface (UPI)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 100000.0, "daily_limit": 100000.0, "per_txn_fee_flat": 0.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "IMPS", "rail_name": "Immediate Payment Service (IMPS)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 500000.0, "daily_limit": 500000.0, "per_txn_fee_flat": 5.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "NEFT", "rail_name": "National Electronic Funds Transfer (NEFT)", "country_code": "IN", "currency": "INR", "min_amount": 1.0, "max_amount": 10000000.0, "daily_limit": 10000000.0, "per_txn_fee_flat": 2.5, "per_txn_fee_percent": 0.0, "is_instant": False, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "RTGS", "rail_name": "Real Time Gross Settlement (RTGS)", "country_code": "IN", "currency": "INR", "min_amount": 200000.0, "max_amount": 50000000.0, "daily_limit": 50000000.0, "per_txn_fee_flat": 25.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "SWIFT", "rail_name": "SWIFT Cross-Border Wire (ISO 20022)", "country_code": "US", "currency": "USD", "min_amount": 10.0, "max_amount": 10000000.0, "daily_limit": 10000000.0, "per_txn_fee_flat": 20.0, "per_txn_fee_percent": 0.001, "is_instant": False, "is_cross_border": True, "sandbox_mode": True},
        {"rail_code": "SEPA", "rail_name": "SEPA Instant Credit Transfer", "country_code": "EU", "currency": "EUR", "min_amount": 1.0, "max_amount": 100000.0, "daily_limit": 100000.0, "per_txn_fee_flat": 0.5, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "ACH", "rail_name": "Automated Clearing House (ACH)", "country_code": "US", "currency": "USD", "min_amount": 1.0, "max_amount": 250000.0, "daily_limit": 250000.0, "per_txn_fee_flat": 0.25, "per_txn_fee_percent": 0.0, "is_instant": False, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "FEDWIRE", "rail_name": "Fedwire Funds Service", "country_code": "US", "currency": "USD", "min_amount": 1.0, "max_amount": 50000000.0, "daily_limit": 50000000.0, "per_txn_fee_flat": 15.0, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
        {"rail_code": "FASTER_PAYMENTS", "rail_name": "UK Faster Payments (FPS)", "country_code": "GB", "currency": "GBP", "min_amount": 1.0, "max_amount": 1000000.0, "daily_limit": 1000000.0, "per_txn_fee_flat": 0.2, "per_txn_fee_percent": 0.0, "is_instant": True, "is_cross_border": False, "sandbox_mode": True},
    ]
    for r in default_rails:
        if not db.query(PaymentRailConfig).filter(PaymentRailConfig.rail_code == r["rail_code"]).first():
            db.add(PaymentRailConfig(**r))
    db.commit()

    # 4. Seed Roles
    roles = {}
    for r in ROLES:
        role = db.query(Role).filter(Role.name == r["name"]).first()
        if not role:
            role = Role(name=r["name"], description=r["description"])
            db.add(role)
            db.flush()
        roles[r["name"]] = role
    db.commit()

    # 5. Seed Users
    users_data = [
        {"email": "admin@fedbank.com", "full_name": "Chief Executive Admin", "role": "SUPER_ADMIN", "pass": "Admin@123"},
        {"email": "banka.admin@fedbank.com", "full_name": "Alpha Bank Administrator", "role": "BANK_ADMIN", "pass": "BankA@123"},
        {"email": "bankb.admin@fedbank.com", "full_name": "Beta Bank Administrator", "role": "BANK_ADMIN", "pass": "BankB@123"},
        {"email": "data.scientist@fedbank.com", "full_name": "Lead Financial Data Scientist", "role": "DATA_SCIENTIST", "pass": "DataSci@123"},
        {"email": "ml.engineer@fedbank.com", "full_name": "Chief MLOps Engineer", "role": "ML_ENGINEER", "pass": "MLEng@123"},
        {"email": "auditor@fedbank.com", "full_name": "Senior Compliance Auditor", "role": "AUDITOR", "pass": "Auditor@123"},
        {"email": "viewer@fedbank.com", "full_name": "Read-Only Executive Viewer", "role": "VIEWER", "pass": "Viewer@123"},
        {"email": "customer@fedbank.com", "full_name": "Rajesh Kumar (Customer)", "role": "CUSTOMER", "pass": "Customer@123"},
    ]
    users = {}
    for u in users_data:
        user = db.query(User).filter(User.email == u["email"]).first()
        if not user:
            user = User(
                email=u["email"],
                hashed_password=hash_password(u["pass"]),
                full_name=u["full_name"],
                role_id=roles[u["role"]].id,
                is_active=True,
            )
            db.add(user)
            db.flush()
        users[u["email"]] = user
    db.commit()

    # 6. Seed Banks
    banks = {}
    for b in BANKS:
        bank = db.query(Bank).filter(Bank.code == b["code"]).first()
        if not bank:
            bank = Bank(
                name=b["name"],
                code=b["code"],
                branch=b["branch"],
                contact_person=b["contact_person"],
                email=b["email"],
                phone=b["phone"],
                location=b["location"],
                country_code=b.get("country_code", "IN"),
                num_customers=b["num_customers"],
                dataset_size=b["dataset_size"],
                current_model_version=b["current_model_version"],
                accuracy=b["accuracy"],
                participation_status=b["participation_status"],
            )
            db.add(bank)
            db.flush()
        banks[b["code"]] = bank
    db.commit()

    # 7. Seed Branches
    branch_seeds = [
        {"bank": "BANK-001", "code": "BR-MUM-01", "name": "Nariman Point Branch", "ifsc": "ALPH0001001", "micr": "400024001", "city": "Mumbai", "state": "Maharashtra"},
        {"bank": "BANK-002", "code": "BR-DEL-01", "name": "Connaught Place Branch", "ifsc": "BETA0002001", "micr": "110024001", "city": "New Delhi", "state": "Delhi"},
        {"bank": "BANK-003", "code": "BR-BLR-01", "name": "Whitefield Tech Branch", "ifsc": "GAMM0003001", "micr": "560024001", "city": "Bengaluru", "state": "Karnataka"},
        {"bank": "BANK-004", "code": "BR-HYD-01", "name": "HITEC City Branch", "ifsc": "DELT0004001", "micr": "500024001", "city": "Hyderabad", "state": "Telangana"},
    ]
    branches = {}
    for br in branch_seeds:
        branch = db.query(Branch).filter(Branch.code == br["code"]).first()
        if not branch:
            branch = Branch(
                bank_id=banks[br["bank"]].id,
                code=br["code"],
                name=br["name"],
                ifsc_code=br["ifsc"],
                micr_code=br["micr"],
                city=br["city"],
                state=br["state"],
                country_code="IN",
            )
            db.add(branch)
            db.flush()
        branches[br["code"]] = branch
    db.commit()

    # 8. Seed Customers & Accounts
    customer_seeds = [
        {"num": "CUST-IN-001", "bank": "BANK-001", "fn": "Rajesh", "ln": "Kumar", "email": "rajesh.kumar@example.in", "phone": "9876543210", "city": "Mumbai", "pan": "ABCDE1234F", "income": 1200000.0, "score": 780, "vpa": "rajesh@fedbank", "bal": 145000.0},
        {"num": "CUST-IN-002", "bank": "BANK-002", "fn": "Priya", "ln": "Sharma", "email": "priya.sharma@example.in", "phone": "9811223344", "city": "New Delhi", "pan": "BFGPS5678K", "income": 950000.0, "score": 745, "vpa": "priya@fedbank", "bal": 82000.0},
        {"num": "CUST-IN-003", "bank": "BANK-003", "fn": "Vikram", "ln": "Nair", "email": "vikram.nair@example.in", "phone": "9944556677", "city": "Bengaluru", "pan": "CRTNQ9012L", "income": 1800000.0, "score": 810, "vpa": "vikram@fedbank", "bal": 320000.0},
        {"num": "CUST-IN-004", "bank": "BANK-004", "fn": "Ananya", "ln": "Reddy", "email": "ananya.reddy@example.in", "phone": "9700112233", "city": "Hyderabad", "pan": "DFTRP3456M", "income": 850000.0, "score": 720, "vpa": "ananya@fedbank", "bal": 64000.0},
        {"num": "CUST-US-001", "bank": "BANK-001", "fn": "John", "ln": "Miller", "email": "john.miller@example.com", "phone": "12125550199", "city": "New York", "pan": None, "income": 125000.0, "score": 790, "vpa": "jmiller@fedbank", "bal": 42000.0, "cur": "USD", "country": "US"},
    ]

    for cs in customer_seeds:
        c = db.query(Customer).filter(Customer.customer_number == cs["num"]).first()
        if not c:
            c = Customer(
                bank_id=banks[cs["bank"]].id,
                customer_number=cs["num"],
                customer_type="INDIVIDUAL",
                first_name=cs["fn"],
                last_name=cs["ln"],
                email=cs["email"],
                phone=cs["phone"],
                country_code=cs.get("country", "IN"),
                city=cs["city"],
                pan_number=cs.get("pan"),
                annual_income=cs["income"],
                credit_score=cs["score"],
                credit_risk_tier="LOW_RISK" if cs["score"] >= 750 else "MEDIUM_RISK",
                customer_segment="RETAIL",
                kyc_status="VERIFIED",
                aml_status="CLEAR",
                account_status="ACTIVE",
            )
            db.add(c)
            db.flush()

            # Add Account
            acc_num = f"1001{uuid.uuid4().hex[:8]}"
            currency = cs.get("cur", "INR")
            acc = Account(
                customer_id=c.id,
                bank_id=banks[cs["bank"]].id,
                account_number=acc_num,
                account_type="SAVINGS",
                currency=currency,
                balance=cs["bal"],
                available_balance=cs["bal"],
                ledger_balance=cs["bal"],
                upi_vpa=cs["vpa"],
                status="ACTIVE",
            )
            db.add(acc)
            db.flush()

            # Add Card
            card = Card(
                customer_id=c.id,
                account_id=acc.id,
                bank_id=banks[cs["bank"]].id,
                card_number_masked=f"6071-XXXX-XXXX-{cs['phone'][-4:]}",
                card_token=f"tok_{uuid.uuid4().hex}",
                card_type="DEBIT",
                card_network="RUPAY" if currency == "INR" else "VISA",
                cardholder_name=f"{cs['fn']} {cs['ln']}".upper(),
                status="ACTIVE",
            )
            db.add(card)

            # Originate a sample loan for customer 1
            if cs["num"] == "CUST-IN-001":
                LoanService.originate_loan(
                    db=db,
                    customer_id=c.id,
                    bank_id=banks[cs["bank"]].id,
                    loan_type="PERSONAL",
                    principal_amount=500000.0,
                    interest_rate_annual=10.5,
                    tenure_months=36,
                    account_id=acc.id,
                )

            # Add KYC Case
            kyc_case = KYCCase(
                customer_id=c.id,
                case_number=f"KYC-{cs['num']}",
                status="VERIFIED",
                verification_tier="TIER_2_FULL",
                verification_score=98.5,
                pan_verified=True,
                aadhaar_verified=True,
                verified_at=datetime.now(timezone.utc) - timedelta(days=10),
            )
            db.add(kyc_case)

    db.commit()

    # 9. Seed Federated Clients
    for b in BANKS:
        client = db.query(FederatedClient).filter(FederatedClient.bank_id == banks[b["code"]].id).first()
        if not client:
            client = FederatedClient(
                bank_id=banks[b["code"]].id,
                name=f"{b['name']} FL Node",
                status="ONLINE",
                current_round=10,
                local_accuracy=b["accuracy"],
                local_loss=0.22,
                training_status="IDLE",
            )
            db.add(client)
    db.commit()

    # 10. Seed System Settings
    for s in DEFAULT_SETTINGS:
        setting = db.query(SystemSetting).filter(SystemSetting.key == s["key"]).first()
        if not setting:
            setting = SystemSetting(key=s["key"], value=s["value"], description=s["description"], category=s["category"])
            db.add(setting)
    db.commit()

    # 11. Seed ML Baseline Model
    m = db.query(MLModel).filter(MLModel.name == "FedBank Credit Risk Ensemble").first()
    if not m:
        m = MLModel(
            name="FedBank Credit Risk Ensemble",
            use_case="credit_risk",
            algorithm="random_forest",
            description="Production federated Random Forest ensemble for credit default risk",
        )
        db.add(m)
        db.flush()

        v = ModelVersion(
            model_id=m.id,
            version="v2.1.0",
            accuracy=0.886,
            precision_score=0.865,
            recall=0.848,
            f1=0.856,
            auc=0.923,
            loss=0.215,
            status="PRODUCTION",
            deployment_status="ACTIVE",
            confusion_matrix=json.dumps([[1490, 110], [95, 805]]),
            feature_importance=json.dumps({
                "debt_to_income": 0.289,
                "credit_score": 0.214,
                "account_balance": 0.148,
                "income": 0.125,
                "loan_amount": 0.084,
            }),
            created_by=users["ml.engineer@fedbank.com"].id,
            approved_by=users["admin@fedbank.com"].id,
            approved_at=datetime.now(timezone.utc) - timedelta(days=2),
            approval_reason="Passed 85% F1 threshold across all 4 federated nodes",
        )
        db.add(v)
        db.commit()

    logger.info("Database seeding complete!")
