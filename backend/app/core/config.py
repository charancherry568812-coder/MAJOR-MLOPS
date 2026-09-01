"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment."""

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./fedbank.db"

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET: str = "change-this-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRATION: int = 30  # minutes
    JWT_REFRESH_EXPIRATION: int = 10080  # minutes (7 days)

    # ── MLflow ────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "./mlruns"

    # ── Federated Learning ────────────────────────────────────
    FEDERATED_SERVER_HOST: str = "0.0.0.0"
    FEDERATED_SERVER_PORT: int = 8080

    # ── Storage Paths ─────────────────────────────────────────
    MODEL_STORAGE_PATH: str = "./model_storage"
    REPORT_STORAGE_PATH: str = "./report_storage"
    DATASET_STORAGE_PATH: str = "./dataset_storage"

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
