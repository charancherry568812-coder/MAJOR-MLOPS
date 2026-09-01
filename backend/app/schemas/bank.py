"""Bank Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BankCreate(BaseModel):
    name: str = Field(..., min_length=1)
    code: str = Field(..., min_length=2, max_length=10)
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


class BankUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class BankResponse(BaseModel):
    id: str
    name: str
    code: str
    contact_person: str
    email: str
    phone: str
    location: str
    status: str
    client_count: int = 0
    dataset_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
