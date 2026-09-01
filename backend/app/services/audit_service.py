"""Audit logging helper."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user=None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    status: str = "SUCCESS",
) -> None:
    """Create an audit log entry."""
    try:
        log = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            user_role=user.role.name if user and user.role else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}),
            ip_address=ip_address,
            status=status,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        db.rollback()
