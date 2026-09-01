"""Import all models so SQLAlchemy registers them."""

from app.models.user import User, Role  # noqa: F401
from app.models.banking_country import Country, Currency, BankingRegulation, PaymentRailConfig  # noqa: F401
from app.models.bank import Bank, BankUser  # noqa: F401
from app.models.branch import Branch  # noqa: F401
from app.models.customer import Customer, CustomerProfile  # noqa: F401
from app.models.account import Account, Beneficiary  # noqa: F401
from app.models.transaction_payment import Transaction, Payment, UPIPaymentIntent  # noqa: F401
from app.models.loan import Loan, LoanPayment  # noqa: F401
from app.models.card import Card  # noqa: F401
from app.models.kyc_aml_sanctions import KYCCase, KYCDocument, AMLAlert, AMLCase, SanctionsWatchlist, SanctionsMatch  # noqa: F401
from app.models.async_job import AsyncJob  # noqa: F401
from app.models.drift_quality import AdvancedDataDriftReport, ModelDriftReport, ConceptDriftReport  # noqa: F401
from app.models.client import FederatedClient  # noqa: F401
from app.models.dataset import Dataset, DatasetVersion, DataQualityReport  # noqa: F401
from app.models.experiment import Experiment, TrainingRun, TrainingRound  # noqa: F401
from app.models.ml_model import MLModel, ModelVersion, ModelMetrics  # noqa: F401
from app.models.deployment import Deployment  # noqa: F401
from app.models.prediction import Prediction, PredictionBatch  # noqa: F401
from app.models.monitoring import MonitoringMetric, DriftReport  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.settings import SystemSetting  # noqa: F401
from app.models.fraud import FraudAlert  # noqa: F401
from app.models.system_event import SystemEvent  # noqa: F401
