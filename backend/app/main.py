"""FedBank MLOps — FastAPI Application Entry Point."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure Matplotlib cache stays within workspace
os.environ["MPLCONFIGDIR"] = str(Path(__file__).resolve().parents[2] / ".matplotlib_cache")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.database.init_db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fedbank")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()
    # Create storage directories
    for d in [settings.MODEL_STORAGE_PATH, settings.REPORT_STORAGE_PATH, settings.DATASET_STORAGE_PATH]:
        Path(d).mkdir(parents=True, exist_ok=True)
    # Init DB
    init_db()
    logger.info("FedBank MLOps API started successfully")
    yield
    logger.info("FedBank MLOps API shutting down")


app = FastAPI(
    title="FedBank MLOps – Federated Machine Learning & MLOps Platform for Banking",
    description="Enterprise Global & India-First Privacy-Preserving Federated ML & MLOps Banking Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID Middleware ─────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Global Exception Handlers ────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": f"HTTP_{exc.status_code}", "message": exc.detail},
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"},
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ── Import Routers ───────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.banks import router as banks_router
from app.api.clients import router as clients_router
from app.api.datasets import router as datasets_router
from app.api.federated import router as federated_router
from app.api.models import router as models_router
from app.api.predictions import router as predictions_router
from app.api.fraud import router as fraud_router
from app.api.pipeline import router as pipeline_router

# Banking & Enterprise Routers
from app.api.banking_countries import countries_router, currencies_router, rails_router
from app.api.customers import customers_router
from app.api.accounts import accounts_router
from app.api.transactions import transactions_router, payments_router
from app.api.loans import loans_router
from app.api.cards import cards_router
from app.api.kyc import kyc_router
from app.api.aml_sanctions import aml_router, sanctions_router
from app.api.jobs import jobs_router
from app.api.drift_quality_routes import drift_router, quality_router

from app.api.all_routers import (
    monitoring_router, alerts_router, audit_router, dashboard_router,
    sse_router, settings_router, notifications_router, users_router,
    experiments_router, training_runs_router, reports_router,
    deployments_router, security_router,
)

# System health and root
app.include_router(health_router)
app.include_router(health_router, prefix="/api")
app.include_router(health_router, prefix="/api/v1")

# Mount both /api/v1 and /api prefixes for full OpenAPI compatibility
for pfx in ["/api/v1", "/api"]:
    # Core & Auth
    app.include_router(auth_router, prefix=pfx)
    app.include_router(users_router, prefix=pfx)
    app.include_router(dashboard_router, prefix=pfx)

    # Banking & International Rails
    app.include_router(countries_router, prefix=pfx)
    app.include_router(currencies_router, prefix=pfx)
    app.include_router(rails_router, prefix=pfx)
    app.include_router(banks_router, prefix=pfx)
    app.include_router(customers_router, prefix=pfx)
    app.include_router(accounts_router, prefix=pfx)
    app.include_router(transactions_router, prefix=pfx)
    app.include_router(payments_router, prefix=pfx)
    app.include_router(loans_router, prefix=pfx)
    app.include_router(cards_router, prefix=pfx)

    # Risk, Compliance & KYC/AML/Sanctions
    app.include_router(kyc_router, prefix=pfx)
    app.include_router(aml_router, prefix=pfx)
    app.include_router(sanctions_router, prefix=pfx)
    app.include_router(fraud_router, prefix=pfx)
    app.include_router(predictions_router, prefix=pfx)

    # ML & Federated Learning
    app.include_router(datasets_router, prefix=pfx)
    app.include_router(federated_router, prefix=pfx)
    app.include_router(models_router, prefix=pfx)
    app.include_router(pipeline_router, prefix=pfx)
    app.include_router(clients_router, prefix=pfx)
    app.include_router(experiments_router, prefix=pfx)
    app.include_router(training_runs_router, prefix=pfx)
    app.include_router(deployments_router, prefix=pfx)

    # Drift & Quality
    app.include_router(drift_router, prefix=pfx)
    app.include_router(quality_router, prefix=pfx)

    # Async Jobs, Monitoring, Audit & System
    app.include_router(jobs_router, prefix=pfx)
    app.include_router(monitoring_router, prefix=pfx)
    app.include_router(alerts_router, prefix=pfx)
    app.include_router(audit_router, prefix=pfx)
    app.include_router(sse_router, prefix=pfx)
    app.include_router(settings_router, prefix=pfx)
    app.include_router(notifications_router, prefix=pfx)
    app.include_router(reports_router, prefix=pfx)
    app.include_router(security_router, prefix=pfx)

    # Aliases for explicit user prompt URLs
    app.include_router(training_runs_router, prefix=f"{pfx}/training", tags=["Training"])
    app.include_router(audit_router, prefix=f"{pfx}/audit", tags=["Audit"])
    app.include_router(settings_router, prefix=f"{pfx}/system", tags=["System"])


@app.get("/")
def root():
    return {
        "name": "FedBank MLOps API",
        "description": "Enterprise Global & India-First Federated Machine Learning & MLOps Platform for Banking",
        "version": "2.0.0",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }
