"""Client Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    bank_id: str
    name: str = Field(..., min_length=1)
    host: str = "localhost"
    port: int = 8081


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


class ClientResponse(BaseModel):
    id: str
    bank_id: str
    bank_name: str = ""
    name: str
    status: str
    host: str
    port: int
    last_heartbeat: Optional[datetime] = None
    current_round: int = 0
    dataset_version: Optional[str] = None
    local_accuracy: Optional[float] = None
    local_loss: Optional[float] = None
    training_status: str = "IDLE"
    created_at: datetime

    class Config:
        from_attributes = True
