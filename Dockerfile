# Multi-stage Dockerfile for FedBank MLOps Backend
FROM python:3.9-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/backend:/app
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/app/.matplotlib_cache

COPY backend /app/backend
COPY federated /app/federated
COPY ml /app/ml
COPY mlops /app/mlops
COPY scripts /app/scripts
COPY dataset_storage /app/dataset_storage
COPY model_storage /app/model_storage

RUN mkdir -p /app/.matplotlib_cache /app/report_storage /app/mlruns

EXPOSE 8000 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
