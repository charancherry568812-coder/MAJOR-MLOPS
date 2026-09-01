"""Card Management & Tokenization Security API Router."""

from __future__ import annotations

import random
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.account import Account
from app.models.card import Card
from app.schemas.banking import CardIssueRequest

cards_router = APIRouter(prefix="/cards", tags=["Cards"])


@cards_router.get("")
def list_cards(
    customer_id: Optional[str] = None,
    account_id: Optional[str] = None,
    card_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Card)
    if customer_id:
        query = query.filter(Card.customer_id == customer_id)
    if account_id:
        query = query.filter(Card.account_id == account_id)
    if card_type:
        query = query.filter(Card.card_type == card_type.upper())

    cards = query.all()
    return {"success": True, "data": [{
        "id": c.id,
        "customer_id": c.customer_id,
        "account_id": c.account_id,
        "card_number_masked": c.card_number_masked,
        "card_type": c.card_type,
        "card_network": c.card_network,
        "cardholder_name": c.cardholder_name,
        "expiry_month": c.expiry_month,
        "expiry_year": c.expiry_year,
        "credit_limit": c.credit_limit,
        "daily_online_limit": c.daily_online_limit,
        "status": c.status,
        "international_enabled": c.international_enabled,
        "contactless_enabled": c.contactless_enabled,
    } for c in cards]}


@cards_router.post("/issue")
def issue_card(
    req: CardIssueRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    acc = db.query(Account).filter(Account.id == req.account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    # Generate Tokenized synthetic card representation (RuPay prefix: 6071, Visa: 4111, Master: 5200)
    prefix = "6071" if req.card_network.upper() == "RUPAY" else "4111" if req.card_network.upper() == "VISA" else "5200"
    last_four = f"{random.randint(1000, 9999)}"
    masked = f"{prefix}-XXXX-XXXX-{last_four}"
    token = f"tok_pci_{uuid.uuid4().hex}"

    card = Card(
        customer_id=req.customer_id,
        account_id=req.account_id,
        bank_id=req.bank_id,
        card_number_masked=masked,
        card_token=token,
        card_type=req.card_type.upper(),
        card_network=req.card_network.upper(),
        cardholder_name=req.cardholder_name.upper(),
        expiry_month=12,
        expiry_year=2029,
        credit_limit=req.credit_limit if req.card_type.upper() == "CREDIT" else 0.0,
        available_credit=req.credit_limit if req.card_type.upper() == "CREDIT" else 0.0,
        status="ACTIVE",
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return {
        "success": True,
        "data": {
            "id": card.id,
            "card_number_masked": card.card_number_masked,
            "card_type": card.card_type,
            "card_network": card.card_network,
            "status": card.status,
            "token": card.card_token,
        },
    }


@cards_router.post("/{card_id}/toggle-freeze")
def toggle_card_freeze(card_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = "FROZEN" if card.status == "ACTIVE" else "ACTIVE"
    db.commit()

    return {"success": True, "data": {"id": card.id, "status": card.status}}
