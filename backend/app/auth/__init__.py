"""Role-based access control and permissions."""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.bank import BankUser

ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {"*"},
    "ADMIN": {"*"},
    "BANK_ADMIN": {
        "bank:read", "bank:update",
        "client:read", "client:update",
        "dataset:read", "dataset:create", "dataset:update", "dataset:delete",
        "experiment:read", "experiment:create",
        "training:read", "training:create",
        "model:read",
        "prediction:read", "prediction:create",
        "monitoring:read",
        "alert:read",
        "report:read", "report:create",
        "notification:read",
        "dashboard:read",
    },
    "ML_ENGINEER": {
        "experiment:read", "experiment:create", "experiment:update",
        "training:read", "training:create", "training:update",
        "model:read", "model:create", "model:update",
        "dataset:read",
        "monitoring:read",
        "prediction:read", "prediction:create",
        "alert:read",
        "dashboard:read",
    },
    "DATA_SCIENTIST": {
        "dataset:read",
        "experiment:read", "experiment:create",
        "training:read", "training:create",
        "model:read",
        "prediction:read", "prediction:create",
        "monitoring:read",
        "dashboard:read",
    },
    "AUDITOR": {
        "dashboard:read", "bank:read", "client:read", "dataset:read",
        "experiment:read", "training:read", "model:read", "prediction:read",
        "monitoring:read", "alert:read", "report:read", "report:create",
        "audit:read",
    },
    "ANALYST": {
        "dashboard:read",
        "prediction:read", "prediction:create",
        "model:read",
        "report:read", "report:create",
        "monitoring:read",
        "alert:read",
    },
    "VIEWER": {
        "dashboard:read",
        "bank:read",
        "client:read",
        "dataset:read",
        "experiment:read",
        "training:read",
        "model:read",
        "prediction:read",
        "monitoring:read",
        "alert:read",
        "report:read",
    },
}


def check_permission(role_name: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    perms = ROLE_PERMISSIONS.get(role_name, set())
    if "*" in perms:
        return True
    return permission in perms


def get_user_bank_ids(db: Session, user) -> Optional[List[str]]:
    """Get bank IDs accessible by the user. Returns None for super admin (consortium-wide access)."""
    if user.role.name in ("SUPER_ADMIN", "ADMIN", "ML_ENGINEER", "DATA_SCIENTIST", "AUDITOR"):
        return None
    bank_users = db.query(BankUser).filter(BankUser.user_id == user.id).all()
    return [bu.bank_id for bu in bank_users]
