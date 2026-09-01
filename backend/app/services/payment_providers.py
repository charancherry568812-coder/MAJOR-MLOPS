"""Enterprise Payment Provider Interface & Sandbox Implementations for Domestic and International Rails.

Includes:
- UPISandboxProvider (India UPI / NPCI simulation)
- IMPSSandboxProvider (India IMPS 24x7)
- NEFTSandboxProvider (India NEFT)
- RTGSSandboxProvider (India RTGS high-value)
- SWIFTSandboxProvider (International Cross-Border MT103 / ISO 20022)
- SEPASandboxProvider (Eurozone SEPA Credit Transfer)
- ACHSandboxProvider (US ACH clearing)
- FedwireSandboxProvider (US Fedwire real-time)
- FasterPaymentsSandboxProvider (UK Faster Payments)
"""

from __future__ import annotations

import abc
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PaymentExecutionResult:
    success: bool
    status: str  # SUCCESS, PENDING, FAILED, REJECTED
    provider_name: str
    provider_reference: str
    is_sandbox: bool
    fee_applied: float
    clearing_time_ms: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentProvider(abc.ABC):
    """Abstract Base Class for all Banking Payment Rails."""

    def __init__(self, is_sandbox: bool = True):
        self.is_sandbox = is_sandbox

    @property
    @abc.abstractmethod
    def rail_code(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        pass


class UPISandboxProvider(PaymentProvider):
    """India Unified Payments Interface (UPI) Sandbox Provider (NPCI Switch Simulator)."""

    rail_code = "UPI"
    provider_name = "UPISandboxProvider (NPCI Switch Simulator)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        # UPI statutory limit: ₹1,00,000 per standard transaction
        if amount > 100000.0:
            return PaymentExecutionResult(
                success=False,
                status="FAILED",
                provider_name=self.provider_name,
                provider_reference=f"UPI-REJ-{uuid.uuid4().hex[:8].upper()}",
                is_sandbox=True,
                fee_applied=0.0,
                clearing_time_ms=(time.time() - start_t) * 1000,
                error_message="UPI transaction exceeds standard limit of ₹1,00,000 (NPCI Guidelines)",
            )

        # Generate standard 12-digit UPI RRN (Retrieval Reference Number)
        rrn = f"{random.randint(400000000000, 499999999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=f"UPI-{rrn}",
            is_sandbox=True,
            fee_applied=0.0,  # Zero MDR for peer/merchant UPI
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"rrn": rrn, "upi_auth_code": "00", "payer_vpa": sender_id, "payee_vpa": receiver_id},
        )


class IMPSSandboxProvider(PaymentProvider):
    """India Immediate Payment Service (IMPS) 24x7 Sandbox Provider."""

    rail_code = "IMPS"
    provider_name = "IMPSSandboxProvider (National Switch)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        if amount > 500000.0:
            return PaymentExecutionResult(
                success=False,
                status="FAILED",
                provider_name=self.provider_name,
                provider_reference=f"IMPS-REJ-{uuid.uuid4().hex[:8].upper()}",
                is_sandbox=True,
                fee_applied=0.0,
                clearing_time_ms=(time.time() - start_t) * 1000,
                error_message="IMPS limit is ₹5,00,000. Use RTGS for larger amounts.",
            )

        fee = 5.0 if amount < 100000 else 15.0  # Typical IMPS bank fee
        ref = f"IMPS{random.randint(1000000000, 9999999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=ref,
            is_sandbox=True,
            fee_applied=fee,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"reference_number": ref, "ifsc": metadata.get("ifsc", "FEDB0001001") if metadata else "FEDB0001001"},
        )


class NEFTSandboxProvider(PaymentProvider):
    """India National Electronic Funds Transfer (NEFT) Batch Sandbox Provider."""

    rail_code = "NEFT"
    provider_name = "NEFTSandboxProvider (RBI Clearing Engine)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        ref = f"N{datetime.utcnow().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=ref,
            is_sandbox=True,
            fee_applied=2.50,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"batch_number": f"B-{datetime.utcnow().hour}", "utr": ref},
        )


class RTGSSandboxProvider(PaymentProvider):
    """India Real Time Gross Settlement (RTGS) High-Value Sandbox Provider."""

    rail_code = "RTGS"
    provider_name = "RTGSSandboxProvider (RBI Real-Time Core)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        if amount < 200000.0:
            return PaymentExecutionResult(
                success=False,
                status="FAILED",
                provider_name=self.provider_name,
                provider_reference=f"RTGS-REJ-{uuid.uuid4().hex[:8].upper()}",
                is_sandbox=True,
                fee_applied=0.0,
                clearing_time_ms=(time.time() - start_t) * 1000,
                error_message="RTGS minimum statutory transfer amount is ₹2,00,000. Use NEFT/IMPS for smaller amounts.",
            )

        ref = f"R{datetime.utcnow().strftime('%Y%m%d')}{random.randint(1000000, 9999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=ref,
            is_sandbox=True,
            fee_applied=25.0,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"utr": ref, "settlement_cycle": "REAL_TIME_GROSS"},
        )


class SWIFTSandboxProvider(PaymentProvider):
    """International SWIFT MT103 / ISO 20022 Cross-Border Sandbox Provider."""

    rail_code = "SWIFT"
    provider_name = "SWIFTSandboxProvider (ISO 20022 Gateway)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        uetr = str(uuid.uuid4())  # Unique End-to-End Transaction Reference (UETR)
        swift_bic = metadata.get("swift_bic", "FEDBUS33XXX") if metadata else "FEDBUS33XXX"
        
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=f"SWIFT-{uetr[:18].upper()}",
            is_sandbox=True,
            fee_applied=20.0,  # $20 SWIFT cable charge
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={
                "uetr": uetr,
                "message_type": "pacs.008.001.08 (ISO 20022)",
                "correspondent_bic": swift_bic,
                "charges": "SHA",
            },
        )


class SEPASandboxProvider(PaymentProvider):
    """Eurozone Single Euro Payments Area (SEPA Credit Transfer) Sandbox Provider."""

    rail_code = "SEPA"
    provider_name = "SEPASandboxProvider (EBA CLEARING / STEP2)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        end_to_end_id = f"SEPA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=end_to_end_id,
            is_sandbox=True,
            fee_applied=0.50,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"scheme": "SCT_INSTANT", "end_to_end_id": end_to_end_id},
        )


class ACHSandboxProvider(PaymentProvider):
    """US Automated Clearing House (ACH) Sandbox Provider."""

    rail_code = "ACH"
    provider_name = "ACHSandboxProvider (NACHA Network)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        trace_num = f"{random.randint(100000000000000, 999999999999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=f"ACH-{trace_num[:10]}",
            is_sandbox=True,
            fee_applied=0.25,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"sec_code": "PPD", "trace_number": trace_num},
        )


class FedwireSandboxProvider(PaymentProvider):
    """US Fedwire Funds Service Sandbox Provider."""

    rail_code = "FEDWIRE"
    provider_name = "FedwireSandboxProvider (Federal Reserve FedLine)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        imad = f"{datetime.utcnow().strftime('%Y%m%d')}FEDW{random.randint(100000, 999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=imad,
            is_sandbox=True,
            fee_applied=15.0,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"imad": imad, "omad": f"OMAD-{uuid.uuid4().hex[:8].upper()}"},
        )


class FasterPaymentsSandboxProvider(PaymentProvider):
    """UK Faster Payments System (FPS) Sandbox Provider."""

    rail_code = "FASTER_PAYMENTS"
    provider_name = "FasterPaymentsSandboxProvider (Pay.UK FPS Gateway)"

    def execute_payment(
        self,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        start_t = time.time()
        fps_ref = f"FPS{random.randint(10000000, 99999999)}"
        return PaymentExecutionResult(
            success=True,
            status="SUCCESS",
            provider_name=self.provider_name,
            provider_reference=fps_ref,
            is_sandbox=True,
            fee_applied=0.20,
            clearing_time_ms=(time.time() - start_t) * 1000,
            metadata={"fps_transaction_id": fps_ref},
        )


class PaymentRouter:
    """Dynamic Payment Provider Resolver & Dispatcher."""

    def __init__(self):
        self._providers: Dict[str, PaymentProvider] = {
            "UPI": UPISandboxProvider(),
            "IMPS": IMPSSandboxProvider(),
            "NEFT": NEFTSandboxProvider(),
            "RTGS": RTGSSandboxProvider(),
            "SWIFT": SWIFTSandboxProvider(),
            "SEPA": SEPASandboxProvider(),
            "ACH": ACHSandboxProvider(),
            "FEDWIRE": FedwireSandboxProvider(),
            "FASTER_PAYMENTS": FasterPaymentsSandboxProvider(),
        }

    def get_provider(self, rail_code: str) -> PaymentProvider:
        code = rail_code.upper()
        if code in self._providers:
            return self._providers[code]
        # Default fallback to UPI for domestic or SWIFT for international
        return self._providers["UPI"] if code in ("INTERNAL", "DOMESTIC") else self._providers["SWIFT"]

    def execute(
        self,
        rail_code: str,
        amount: float,
        currency: str,
        sender_id: str,
        receiver_id: str,
        payment_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentExecutionResult:
        provider = self.get_provider(rail_code)
        return provider.execute_payment(
            amount=amount,
            currency=currency,
            sender_id=sender_id,
            receiver_id=receiver_id,
            payment_reference=payment_reference,
            metadata=metadata,
        )


payment_router = PaymentRouter()
