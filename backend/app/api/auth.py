"""Authentication API router."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse, RoleResponse
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        create_audit_log(db, "FAILED_LOGIN", details={"email": req.email}, ip_address=request.client.host if request.client else None, status="FAILURE")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Check account lock
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is locked. Try again later.")

    if not verify_password(req.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
        create_audit_log(db, "FAILED_LOGIN", user=user, ip_address=request.client.host if request.client else None, status="FAILURE")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    # Reset failed attempts on success
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    token_data = {"sub": user.id, "email": user.email, "role": user.role.name}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    create_audit_log(db, "LOGIN", user=user, ip_address=request.client.host if request.client else None)

    user_resp = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": {"id": user.role.id, "name": user.role.name, "description": user.role.description},
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=user_resp)


@router.post("/logout")
def logout(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Log out the current user."""
    create_audit_log(db, "LOGOUT", user=current_user)
    return {"success": True, "message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        token_data = {"sub": user.id, "email": user.email, "role": user.role.name}
        new_access_token = create_access_token(token_data)
        return TokenResponse(access_token=new_access_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    """Get current authenticated user."""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": {"id": current_user.role.id, "name": current_user.role.name, "description": current_user.role.description},
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate password reset token."""
    user = db.query(User).filter(User.email == req.email).first()
    if user:
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        # In production, send email with reset link
        return {"success": True, "message": "If the email exists, a reset link has been sent", "reset_token": token}
    return {"success": True, "message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token."""
    user = db.query(User).filter(User.reset_token == req.token).first()
    if not user or (user.reset_token_expiry and user.reset_token_expiry < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    return {"success": True, "message": "Password reset successfully"}
