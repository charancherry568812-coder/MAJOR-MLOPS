"""Sanctions Screening and Fuzzy Entity Matching Engine."""

from __future__ import annotations

import difflib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.kyc_aml_sanctions import SanctionsMatch, SanctionsWatchlist

# Synthetic Watchlist Entities for Development & Testing
SYNTHETIC_WATCHLIST = [
    {"entity_name": "Viktor Anatoly Chernov", "entity_type": "INDIVIDUAL", "country_code": "RU", "list_source": "OFAC_SYNTHETIC"},
    {"entity_name": "Al-Sham Trading Enterprises", "entity_type": "ENTITY", "country_code": "SY", "list_source": "UN_SANCTIONS_SYNTHETIC"},
    {"entity_name": "Pyongyang Heavy Marine Ltd", "entity_type": "ENTITY", "country_code": "KP", "list_source": "OFAC_SYNTHETIC"},
    {"entity_name": "Farhad Rezaei", "entity_type": "INDIVIDUAL", "country_code": "IR", "list_source": "EU_SANCTIONS_SYNTHETIC"},
    {"entity_name": "Global Shadow Horizon Corp", "entity_type": "ENTITY", "country_code": "CU", "list_source": "OFAC_SYNTHETIC"},
    {"entity_name": "Rajesh Kumar Defaulter Group", "entity_type": "ENTITY", "country_code": "IN", "list_source": "RBI_DEFAULTER_SYNTHETIC"},
]


class SanctionsScreeningService:
    """Fuzzy String Matching and Sanctions Compliance Screening."""

    @staticmethod
    def seed_watchlist_if_empty(db: Session) -> None:
        """Seed baseline synthetic sanctions watchlist."""
        if db.query(SanctionsWatchlist).count() == 0:
            for item in SYNTHETIC_WATCHLIST:
                w = SanctionsWatchlist(
                    entity_name=item["entity_name"],
                    entity_type=item["entity_type"],
                    country_code=item["country_code"],
                    list_source=item["list_source"],
                    aliases=f"{item['entity_name']} Alias, {item['entity_name']} Ltd",
                )
                db.add(w)
            db.commit()

    @staticmethod
    def calculate_similarity(name1: str, name2: str) -> float:
        """Calculate token-sort normalized similarity percentage (0-100)."""
        tokens1 = " ".join(sorted(name1.lower().strip().split()))
        tokens2 = " ".join(sorted(name2.lower().strip().split()))
        seq = difflib.SequenceMatcher(None, tokens1, tokens2)
        return round(seq.ratio() * 100.0, 1)

    @staticmethod
    def screen_entity(
        db: Session,
        query_name: str,
        customer_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        threshold: float = 75.0,
    ) -> List[SanctionsMatch]:
        """Screen query against sanctions database with fuzzy scoring."""
        SanctionsScreeningService.seed_watchlist_if_empty(db)
        watchlist_items = db.query(SanctionsWatchlist).filter(SanctionsWatchlist.is_active == True).all()

        # Resolve valid customer_id
        valid_customer_id = None
        if customer_id:
            c = db.query(Customer).filter(Customer.id == customer_id).first()
            if c:
                valid_customer_id = c.id
        if not valid_customer_id:
            first_c = db.query(Customer).first()
            valid_customer_id = first_c.id if first_c else "CUST-DEFAULT"

        matches: List[SanctionsMatch] = []
        for item in watchlist_items:
            score = SanctionsScreeningService.calculate_similarity(query_name, item.entity_name)
            if score >= threshold:
                match_record = SanctionsMatch(
                    customer_id=valid_customer_id,
                    transaction_id=transaction_id,
                    watchlist_id=item.id,
                    match_score=score,
                    match_type="EXACT" if score >= 98.0 else "FUZZY",
                    status="POTENTIAL_MATCH",
                    review_notes=f"Fuzzy match score: {score}% with watchlist entity '{item.entity_name}' ({item.list_source}).",
                )
                matches.append(match_record)
                db.add(match_record)

        if matches:
            db.commit()

        return matches
