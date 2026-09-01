"""KYC Verification & Identity Governance API Router."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.kyc_aml_sanctions import KYCCase, KYCDocument
from app.schemas.banking import AadhaarVerifyRequest, PANVerifyRequest
from app.services.kyc_service import KYCVerificationService

kyc_router = APIRouter(prefix="/kyc", tags=["KYC Identity"])


@kyc_router.get("/cases")
def list_kyc_cases(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(KYCCase)
    if status:
        query = query.filter(KYCCase.status == status.upper())

    total = query.count()
    cases = query.order_by(KYCCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in cases:
        items.append({
            "id": c.id,
            "case_number": c.case_number,
            "customer_id": c.customer_id,
            "customer_name": f"{c.customer.first_name} {c.customer.last_name}" if c.customer else "",
            "status": c.status,
            "verification_provider": c.verification_provider,
            "verification_score": c.verification_score,
            "pan_verified": c.pan_verified,
            "aadhaar_verified": c.aadhaar_verified,
            "risk_flags": c.risk_flags,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"success": True, "data": {"total": total, "page": page, "items": items}}


@kyc_router.post("/verify-pan")
def verify_pan(req: PANVerifyRequest):
    """Sandbox PAN Verification adapter (NSDL/Income Tax Department simulator)."""
    res = KYCVerificationService.verify_pan_sandbox(req.pan_number, req.full_name)
    return {"success": True, "data": res}


@kyc_router.post("/verify-aadhaar")
def verify_aadhaar(req: AadhaarVerifyRequest):
    """Sandbox Aadhaar OTP / Demographic adapter (UIDAI Gateway simulator)."""
    res = KYCVerificationService.verify_aadhaar_sandbox(req.aadhaar_number, req.full_name)
    return {"success": True, "data": res}


@kyc_router.post("/process-case/{customer_id}")
def process_customer_kyc(
    customer_id: str,
    pan_number: Optional[str] = None,
    aadhaar_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN", "SUPER_ADMIN"])),
):
    try:
        case = KYCVerificationService.process_kyc_case(
            db=db,
            customer_id=customer_id,
            pan_number=pan_number,
            aadhaar_number=aadhaar_number,
            reviewer_id=current_user.id,
        )
        return {
            "success": True,
            "data": {
                "case_id": case.id,
                "case_number": case.case_number,
                "status": case.status,
                "verification_score": case.verification_score,
                "verified_at": case.verified_at.isoformat() if case.verified_at else None,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
