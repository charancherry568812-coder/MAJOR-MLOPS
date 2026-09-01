# 🏦 FedBank MLOps – Federated Machine Learning & MLOps Platform for Banking

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com)
[![Flower](https://img.shields.io/badge/Flower-FL_1.7+-ff69b4.svg)](https://flower.ai)
[![MLflow](https://img.shields.io/badge/MLflow-2.10+-0194E2.svg)](https://mlflow.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6+-646CFF.svg)](https://vitejs.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, privacy-preserving **Federated Machine Learning and MLOps Platform** engineered specifically for the financial and banking sector. **FedBank MLOps** enables multi-bank consortia to collaboratively train production ML models (Credit Risk Scoring, Fraud Detection, Customer Churn, AML) **without sharing raw customer banking records**.

---

## 📑 Table of Contents
1. [Core Architectural Philosophy](#-core-architectural-philosophy)
2. [End-to-End System Architecture](#-end-to-end-system-architecture)
3. [Bank Consortia & Synthetic Data Generation](#-bank-consortia--synthetic-data-generation)
4. [Federated Learning & FedAvg Aggregation](#-federated-learning--fedavg-aggregation)
5. [MLOps Lifecycle & Visual Pipeline](#-mlops-lifecycle--visual-pipeline)
6. [Role-Based Access Control & Demo Accounts](#-role-based-access-control--demo-accounts)
7. [REST API Documentation](#-rest-api-documentation)
8. [Automated Test Suite](#-automated-test-suite)
9. [Quickstart: Running Locally](#-quickstart-running-locally)
10. [Docker Deployment](#-docker-deployment)

---

## 🔒 Core Architectural Philosophy

In traditional banking machine learning, institutions face a strict regulatory barrier: **GDPR, CCPA, and banking secrecy laws strictly forbid sharing raw customer PII across corporate boundaries**. 

FedBank MLOps resolves this via decentralized **Federated Learning**:
* **Decentralized Data**: Customer profiles, credit scores, debt obligations, and transaction histories are stored exclusively in isolated bank nodes (`BANK-001` through `BANK-004`).
* **Local Model Fitting**: Each participating bank trains local models (Logistic Regression, Random Forest, XGBoost) only on its local customer partition.
* **Weight & Metric Sharing**: Local banks submit **only mathematical model parameters and evaluation loss** to the central FedBank MLOps server.
* **Secure FedAvg Aggregation**: The central coordinator performs sample-weighted parameter averaging (FedAvg), validates the unified global model against an objective holdout benchmark, and logs the artifact to the MLflow Model Registry.

---

## 🏛 End-to-End System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │       FedBank MLOps Central Server      │
                               │  FastAPI • Flower FedAvg • MLflow • SSE │
                               └────────────────────┬────────────────────┘
                                                    │
                 ┌───────────────────┬──────────────┴───────┬───────────────────┐
                 │                   │                      │                   │
                 ▼                   ▼                      ▼                   ▼
        ┌─────────────────┐ ┌─────────────────┐    ┌─────────────────┐ ┌─────────────────┐
        │  Alpha Nat Bank │ │  Beta Fed Bank  │    │ Gamma Trust Bank│ │ Delta Sav Bank  │
        │   (BANK-001)    │ │   (BANK-002)    │    │   (BANK-003)    │ │   (BANK-004)    │
        │  5,000 Records  │ │  4,500 Records  │    │  6,000 Records  │ │  5,500 Records  │
        └─────────────────┘ └─────────────────┘    └─────────────────┘ └─────────────────┘
```

The platform consists of:
* **Frontend**: Responsive React 18, TypeScript, Tailwind CSS, Recharts, Vite, React Query.
* **Backend**: FastAPI with async route execution, SQLAlchemy ORM, Alembic migrations, SQLite/PostgreSQL support.
* **Federated Learning**: Flower (`flwr`) framework and high-performance in-process simulation engine supporting FedAvg aggregation and live progress broadcasts.
* **MLflow & Model Registry**: Automated experiment runs, parameter tracking, model artifact versioning, and stage promotions (`REGISTERED` → `STAGING` → `PRODUCTION`).
* **Real-time Event Streaming**: Server-Sent Events (SSE) broadcasting training round metrics, node heartbeats, and pipeline step logs directly to the dashboard.
* **Fraud Detection & AML**: Real-time transaction scoring engine with velocity tracking, device multiplicity evaluation, and interactive alert resolution workflows.

---

## 📊 Bank Consortia & Synthetic Data Generation

FedBank MLOps generates **21,000 synthetic banking records** with realistic financial distributions, covariance structures, and target labels.

| Bank Code | Bank Name | Customer Portfolio | Features Included |
|---|---|---|---|
| **BANK-001** | Alpha National Bank | 5,000 customers | Credit risk, loans, debt-to-income, account balances |
| **BANK-002** | Beta Federal Bank | 4,500 customers | Credit risk, payment defaults, transaction velocity |
| **BANK-003** | Gamma Trust Bank | 6,000 customers | Credit risk, wealth assets, loan terms, churn flags |
| **BANK-004** | Delta Savings Bank | 5,500 customers | Credit risk, savings balances, delinquency history |

To regenerate synthetic datasets at any time:
```bash
PYTHONPATH=backend python3 scripts/generate_data.py
```

---

## 🤖 Federated Learning & FedAvg Aggregation

The platform supports both socket-based gRPC Flower clients (`federated/flower_server.py`, `federated/flower_client.py`) and integrated async simulations (`federated/simulation.py`).

### Federated Averaging (FedAvg) Formula:
$$\theta_{\text{global}} = \sum_{k=1}^{K} \frac{n_k}{N} \theta_k$$

Where:
* $K$ is the number of participating bank nodes ($K=4$).
* $n_k$ is the number of local training records at Bank $k$.
* $N = \sum n_k$ is the total dataset volume across all banks ($N=21,000$).
* $\theta_k$ represents the localized model weight vector.

---

## ⚙️ MLOps Lifecycle & Visual Pipeline

The `/pipeline` page provides an interactive, visual 11-stage orchestrator:

1. **Data Ingestion**: Multi-bank customer records ingested from local node storage.
2. **Data Validation**: Schema validation, missing values, duplicates, and outlier analysis.
3. **Feature Preprocessing**: Median imputation, standard scaling, and alias alignment.
4. **Local Node Training**: Decentralized model fitting on private partitions.
5. **Federated Parameter Exchange**: Local nodes submit model weights over gRPC/memory.
6. **Secure Aggregation**: Sample-weighted FedAvg parameter consolidation.
7. **Global Model Synthesis**: Production checkpoint generated from aggregated parameters.
8. **Holdout Evaluation**: Cross-bank holdout verification (Accuracy, F1, ROC-AUC).
9. **MLflow Registry**: Experiment run logging and model version registration.
10. **Zero-Downtime Deployment**: Dynamic model server update without restarting services.
11. **Continuous Monitoring**: Live tracking of Population Stability Index (PSI) and data drift.

---

## 👥 Role-Based Access Control & Demo Accounts

The database comes pre-seeded with 7 demo accounts representing all banking governance personas:

| Role | Email | Password | Permissions |
|---|---|---|---|
| **SUPER_ADMIN** | `admin@fedbank.com` | `Admin@123` | Master access across all consortia banks, pipeline, models, and settings |
| **BANK_ADMIN** | `banka.admin@fedbank.com` | `BankA@123` | Local bank management for Alpha National Bank (BANK-001) |
| **BANK_ADMIN** | `bankb.admin@fedbank.com` | `BankB@123` | Local bank management for Beta Federal Bank (BANK-002) |
| **DATA_SCIENTIST** | `data.scientist@fedbank.com` | `DataSci@123` | Dataset exploration, experimentation, training runs, predictions |
| **ML_ENGINEER** | `ml.engineer@fedbank.com` | `MLEng@123` | Model training, MLOps pipeline execution, model registry promotions |
| **AUDITOR** | `auditor@fedbank.com` | `Auditor@123` | Read-only compliance inspection, immutable audit logs, report generation |
| **VIEWER** | `viewer@fedbank.com` | `Viewer@123` | Read-only dashboard and model metric overview |

---

## 🌐 REST API Documentation

Once the server is running, the interactive OpenAPI Swagger documentation is available at:
`http://localhost:8000/docs`

Key route groups:
* `/api/v1/auth/*`: Authentication, login, token refresh, and profile management.
* `/api/v1/users/*`: User account provisioning and role assignments.
* `/api/v1/banks/*`: Bank node registration, customer volume, and performance tracking.
* `/api/v1/datasets/*`: Dataset ingestion, quality reporting, and schema verification.
* `/api/v1/federated/*`: Federated learning training runs, client node status, and round metrics.
* `/api/v1/pipeline/*`: MLOps 11-stage pipeline execution, start, stop, retrain, and deploy.
* `/api/v1/models/*`: MLflow Model Registry, version comparison, and stage promotion.
* `/api/v1/predictions/*`: Credit risk scoring and SHAP feature importance explanations.
* `/api/v1/fraud/*`: Transaction fraud scoring, velocity evaluation, and alert resolution.
* `/api/v1/monitoring/*`: Population Stability Index (PSI), performance drift, and system health.
* `/api/v1/audit-logs`: Immutable regulatory compliance audit trails.
* `/api/v1/reports/*`: Downloadable CSV and PDF compliance digests.
* `/api/v1/settings/*`: System governance parameters and drift alert thresholds.

---

## 🧪 Automated Test Suite

The platform includes a comprehensive automated test suite covering all operational modules:

```bash
PYTHONPATH=backend .venv/bin/pytest tests/ -v
```

Test Results:
* `tests/test_auth.py`: 4 tests (SuperAdmin login, demo role authentication, token refresh, invalid credentials).
* `tests/test_banks.py`: 3 tests (Bank listing, detail inspection, dynamic creation).
* `tests/test_datasets.py`: 2 tests (Multi-bank dataset listing, quality score verification).
* `tests/test_federated.py`: 1 test (Multi-round federated learning with FedAvg aggregation).
* `tests/test_ml_pipeline.py`: 2 tests (Preprocessor fit/transform, model training and metrics).
* `tests/test_predictions_fraud.py`: 2 tests (Credit risk inference with SHAP, transaction fraud scoring and alert resolution).
* `tests/test_smoke_e2e.py`: 1 test (Full platform end-to-end smoke verification).

**Status**: 15 passed, 0 failed.

---

## 🚀 Quickstart: Running Locally

The entire platform runs on your local machine without requiring cloud accounts or paid services:

### 1. Launch Platform
```bash
./start.sh
```
This script will:
1. Activate the Python virtual environment.
2. Generate 21,000 synthetic banking records across 4 banks.
3. Initialize and seed the database with all demo roles and accounts.
4. Launch the FastAPI backend on `http://localhost:8000`.
5. Launch the React frontend on `http://localhost:5173`.

### 2. Access the Platform
* **Web UI**: Open your browser at [http://localhost:5173](http://localhost:5173)
* **Login**: `admin@fedbank.com` / `Admin@123`
* **Swagger API**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Stop the Platform
```bash
./stop.sh
```

---

## 🐳 Docker Deployment

To launch the complete containerized stack using Docker Compose:

```bash
docker-compose up --build -d
```

Services:
* **Frontend Web UI**: `http://localhost:3000`
* **FastAPI Backend**: `http://localhost:8000`
* **MLflow Tracking Server**: `http://localhost:5001`
* **Flower FL gRPC Server**: `localhost:8080`

To shut down:
```bash
docker-compose down
```
