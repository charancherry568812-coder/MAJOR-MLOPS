"""Banks API router."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import check_permission, get_user_bank_ids
from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.bank import Bank
from app.models.client import FederatedClient
from app.models.dataset import Dataset
from app.schemas.bank import BankCreate, BankResponse, BankUpdate
from app.schemas.common import paginated_response
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/banks", tags=["Banks"])

ALL_ROLES = ["SUPER_ADMIN", "ADMIN", "BANK_ADMIN", "ML_ENGINEER", "DATA_SCIENTIST", "AUDITOR", "ANALYST", "VIEWER"]
WRITE_ROLES = ["SUPER_ADMIN", "ADMIN", "BANK_ADMIN"]


@router.get("")
def list_banks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List banks with pagination, search, and filtering."""
    query = db.query(Bank).filter(Bank.is_deleted == False)

    # Bank admin can only see their own banks
    bank_ids = get_user_bank_ids(db, current_user)
    if bank_ids is not None:
        query = query.filter(Bank.id.in_(bank_ids))

    if search:
        query = query.filter(Bank.name.ilike(f"%{search}%") | Bank.code.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Bank.status == status_filter)

    total = query.count()
    banks = query.order_by(Bank.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for b in banks:
        client_count = db.query(FederatedClient).filter(FederatedClient.bank_id == b.id).count()
        dataset_count = db.query(Dataset).filter(Dataset.bank_id == b.id, Dataset.is_deleted == False).count()
        items.append({
            "id": b.id, "name": b.name, "code": b.code,
            "contact_person": b.contact_person, "email": b.email,
            "phone": b.phone, "location": b.location, "status": b.status,
            "client_count": client_count, "dataset_count": dataset_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    return {"success": True, "data": paginated_response(items, total, page, page_size)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_bank(
    req: BankCreate,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(WRITE_ROLES)),
):
    """Create a new bank."""
    existing = db.query(Bank).filter(Bank.code == req.code, Bank.is_deleted == False).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Bank code '{req.code}' already exists")

    bank = Bank(name=req.name, code=req.code, contact_person=req.contact_person,
                email=req.email, phone=req.phone, location=req.location)
    db.add(bank)
    db.commit()
    db.refresh(bank)

    create_audit_log(db, "CREATE", "bank", bank.id, current_user, {"name": bank.name})
    return {"success": True, "data": {"id": bank.id, "name": bank.name, "code": bank.code}}


@router.get("/{bank_id}")
def get_bank(bank_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get bank details."""
    bank = db.query(Bank).filter(Bank.id == bank_id, Bank.is_deleted == False).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    bank_ids = get_user_bank_ids(db, current_user)
    if bank_ids is not None and bank_id not in bank_ids:
        raise HTTPException(status_code=403, detail="Access denied to this bank")

    clients = db.query(FederatedClient).filter(FederatedClient.bank_id == bank_id).all()
    datasets = db.query(Dataset).filter(Dataset.bank_id == bank_id, Dataset.is_deleted == False).all()

    return {
        "success": True,
        "data": {
            "id": bank.id, "name": bank.name, "code": bank.code,
            "contact_person": bank.contact_person, "email": bank.email,
            "phone": bank.phone, "location": bank.location, "status": bank.status,
            "client_count": len(clients), "dataset_count": len(datasets),
            "created_at": bank.created_at.isoformat() if bank.created_at else None,
            "clients": [{"id": c.id, "name": c.name, "status": c.status} for c in clients],
            "datasets": [{"id": d.id, "name": d.name, "status": d.status, "use_case": d.use_case} for d in datasets],
        },
    }


@router.put("/{bank_id}")
def update_bank(
    bank_id: str, req: BankUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(["ADMIN", "BANK_ADMIN"])),
):
    """Update bank details."""
    bank = db.query(Bank).filter(Bank.id == bank_id, Bank.is_deleted == False).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    if current_user.role.name == "BANK_ADMIN":
        bank_ids = get_user_bank_ids(db, current_user)
        if bank_ids and bank_id not in bank_ids:
            raise HTTPException(status_code=403, detail="Access denied")

    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(bank, k, v)
    db.commit()

    create_audit_log(db, "UPDATE", "bank", bank_id, current_user, updates)
    return {"success": True, "data": {"id": bank.id, "name": bank.name}}


@router.delete("/{bank_id}")
def delete_bank(
    bank_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(RoleChecker(WRITE_ROLES)),
):
    """Soft-delete a bank."""
    bank = db.query(Bank).filter(Bank.id == bank_id, Bank.is_deleted == False).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    bank.is_deleted = True
    bank.status = "INACTIVE"
    db.commit()
    create_audit_log(db, "DELETE", "bank", bank_id, current_user, {"name": bank.name})
    return {"success": True, "message": f"Bank '{bank.name}' deleted"}
