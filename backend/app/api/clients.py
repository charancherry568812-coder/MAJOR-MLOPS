"""Federated clients API router."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import RoleChecker, get_current_user, get_db
from app.models.bank import Bank
from app.models.client import FederatedClient
from app.schemas.client import ClientCreate, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("")
def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bank_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(FederatedClient)
    if bank_id:
        query = query.filter(FederatedClient.bank_id == bank_id)
    if status_filter:
        query = query.filter(FederatedClient.status == status_filter)

    total = query.count()
    clients = query.order_by(FederatedClient.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in clients:
        bank = db.query(Bank).filter(Bank.id == c.bank_id).first()
        items.append({
            "id": c.id, "bank_id": c.bank_id, "bank_name": bank.name if bank else "",
            "name": c.name, "status": c.status, "host": c.host, "port": c.port,
            "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
            "current_round": c.current_round, "dataset_version": c.dataset_version,
            "local_accuracy": c.local_accuracy, "local_loss": c.local_loss,
            "training_status": c.training_status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"success": True, "data": {"items": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size)}}


@router.post("", status_code=201)
def create_client(req: ClientCreate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN"]))):
    bank = db.query(Bank).filter(Bank.id == req.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    client = FederatedClient(bank_id=req.bank_id, name=req.name, host=req.host, port=req.port)
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"success": True, "data": {"id": client.id, "name": client.name}}


@router.get("/status-summary")
def client_status_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    clients = db.query(FederatedClient).all()
    summary = {}
    for c in clients:
        summary[c.status] = summary.get(c.status, 0) + 1
    return {"success": True, "data": summary}


@router.get("/{client_id}")
def get_client(client_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(FederatedClient).filter(FederatedClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    bank = db.query(Bank).filter(Bank.id == client.bank_id).first()
    return {"success": True, "data": {
        "id": client.id, "bank_id": client.bank_id, "bank_name": bank.name if bank else "",
        "name": client.name, "status": client.status, "host": client.host, "port": client.port,
        "last_heartbeat": client.last_heartbeat.isoformat() if client.last_heartbeat else None,
        "current_round": client.current_round, "local_accuracy": client.local_accuracy,
        "local_loss": client.local_loss, "training_status": client.training_status,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }}


@router.put("/{client_id}")
def update_client(client_id: str, req: ClientUpdate, db: Session = Depends(get_db), current_user=Depends(RoleChecker(["ADMIN"]))):
    client = db.query(FederatedClient).filter(FederatedClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(client, k, v)
    db.commit()
    return {"success": True, "data": {"id": client.id, "name": client.name}}


@router.post("/{client_id}/heartbeat")
def client_heartbeat(client_id: str, db: Session = Depends(get_db)):
    client = db.query(FederatedClient).filter(FederatedClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.last_heartbeat = datetime.now(timezone.utc)
    if client.status == "OFFLINE":
        client.status = "ONLINE"
    db.commit()
    return {"success": True, "message": "Heartbeat recorded"}
