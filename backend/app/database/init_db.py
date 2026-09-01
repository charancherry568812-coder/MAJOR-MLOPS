"""Initialize database: create tables, run safe migrations, and seed."""

from __future__ import annotations

import logging
from sqlalchemy import text

from app.database import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403  — registers all models
from app.database.seed import seed_database

logger = logging.getLogger(__name__)


def _run_safe_migrations() -> None:
    """Safely apply schema additions to existing tables without data loss."""
    with engine.connect() as conn:
        # Check banks table columns
        try:
            res = conn.execute(text("PRAGMA table_info(banks)")).fetchall()
            existing_cols = {row[1] for row in res}
            if "country_code" not in existing_cols and len(existing_cols) > 0:
                logger.info("Migrating: Adding country_code to banks table")
                conn.execute(text("ALTER TABLE banks ADD COLUMN country_code VARCHAR(2) DEFAULT 'IN'"))
                conn.commit()
        except Exception as e:
            logger.debug(f"Migration check banks: {e}")

        # Check transactions table columns
        try:
            res = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
            existing_cols = {row[1] for row in res}
            if len(existing_cols) > 0:
                cols_to_add = [
                    ("source_account_id", "VARCHAR(36)"),
                    ("destination_account_id", "VARCHAR(36)"),
                    ("customer_id", "VARCHAR(64)"),
                    ("bank_id", "VARCHAR(36)"),
                    ("idempotency_key", "VARCHAR(128)"),
                    ("request_id", "VARCHAR(64)"),
                    ("currency", "VARCHAR(3) DEFAULT 'INR'"),
                    ("fee_amount", "FLOAT DEFAULT 0.0"),
                    ("fx_rate", "FLOAT DEFAULT 1.0"),
                    ("settlement_amount", "FLOAT DEFAULT 0.0"),
                    ("settlement_currency", "VARCHAR(3) DEFAULT 'INR'"),
                    ("payment_rail", "VARCHAR(30) DEFAULT 'UPI'"),
                    ("transaction_type", "VARCHAR(50) DEFAULT 'TRANSFER'"),
                    ("merchant_category", "VARCHAR(100) DEFAULT 'General Retail'"),
                    ("status", "VARCHAR(20) DEFAULT 'COMPLETED'"),
                    ("failure_reason", "VARCHAR(255)"),
                    ("velocity_score", "FLOAT DEFAULT 25.0"),
                    ("amount_deviation", "FLOAT DEFAULT 1.0"),
                    ("num_devices", "INTEGER DEFAULT 1"),
                    ("risk_score", "FLOAT DEFAULT 5.0"),
                    ("fraud_score", "FLOAT DEFAULT 0.02"),
                    ("risk_level", "VARCHAR(20) DEFAULT 'LOW'"),
                    ("is_flagged", "BOOLEAN DEFAULT 0"),
                    ("is_flagged_fraud", "BOOLEAN DEFAULT 0"),
                    ("aml_flag", "BOOLEAN DEFAULT 0"),
                    ("sanctions_check_passed", "BOOLEAN DEFAULT 1"),
                    ("ip_address", "VARCHAR(45) DEFAULT '127.0.0.1'"),
                    ("device_id", "VARCHAR(100) DEFAULT 'dev-primary-mobile'"),
                    ("location_city", "VARCHAR(100) DEFAULT 'Mumbai'"),
                    ("description", "VARCHAR(255) DEFAULT 'Funds transfer'"),
                    ("completed_at", "DATETIME"),
                ]
                for col_name, col_type in cols_to_add:
                    if col_name not in existing_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Migration check transactions: {e}")


def init_db() -> None:
    """Create all tables and seed with demo data."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")

    _run_safe_migrations()

    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error(f"Seeding error: {e}")
        db.rollback()
    finally:
        db.close()
