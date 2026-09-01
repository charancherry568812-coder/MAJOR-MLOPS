"""SQLAlchemy ORM models — Experiment, TrainingRun, TrainingRound."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    use_case = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="ACTIVE")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    training_runs = relationship("TrainingRun", back_populates="experiment")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=True, index=True)
    model_type = Column(String(50), nullable=False)
    use_case = Column(String(50), nullable=False, index=True)
    dataset_version_id = Column(String(36), ForeignKey("dataset_versions.id"), nullable=True)
    federated_strategy = Column(String(50), default="fedavg")
    num_clients = Column(Integer, default=4)
    num_rounds = Column(Integer, default=10)
    local_epochs = Column(Integer, default=5)
    batch_size = Column(Integer, default=32)
    learning_rate = Column(Float, default=0.01)
    hyperparameters = Column(Text, default="{}")  # JSON
    status = Column(String(20), default="QUEUED", index=True)  # QUEUED,RUNNING,COMPLETED,FAILED,STOPPED
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    best_accuracy = Column(Float, nullable=True)
    best_f1 = Column(Float, nullable=True)
    best_auc = Column(Float, nullable=True)
    mlflow_run_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    experiment = relationship("Experiment", back_populates="training_runs")
    rounds = relationship("TrainingRound", back_populates="training_run", order_by="TrainingRound.round_number")


class TrainingRound(Base):
    __tablename__ = "training_rounds"

    id = Column(String(36), primary_key=True, default=_uuid)
    training_run_id = Column(String(36), ForeignKey("training_runs.id"), nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    global_accuracy = Column(Float, nullable=True)
    global_precision = Column(Float, nullable=True)
    global_recall = Column(Float, nullable=True)
    global_f1 = Column(Float, nullable=True)
    global_auc = Column(Float, nullable=True)
    global_loss = Column(Float, nullable=True)
    participating_clients = Column(Integer, default=0)
    total_clients = Column(Integer, default=0)
    client_metrics = Column(Text, default="{}")  # JSON
    aggregation_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    training_run = relationship("TrainingRun", back_populates="rounds")
