"""Experiment and TrainingRun Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    use_case: str = "credit_risk"


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    use_case: str
    status: str
    training_runs_count: int = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingRunCreate(BaseModel):
    experiment_id: Optional[str] = None
    model_type: str = "random_forest"
    use_case: str = "credit_risk"
    dataset_version_id: Optional[str] = None
    federated_strategy: str = "fedavg"
    num_clients: int = Field(default=4, ge=1, le=20)
    num_rounds: int = Field(default=10, ge=1, le=100)
    local_epochs: int = Field(default=5, ge=1, le=50)
    batch_size: int = Field(default=32, ge=8, le=512)
    learning_rate: float = Field(default=0.01, gt=0, le=1.0)


class TrainingRunResponse(BaseModel):
    id: str
    experiment_id: Optional[str] = None
    experiment_name: str = ""
    model_type: str
    use_case: str
    federated_strategy: str
    num_clients: int
    num_rounds: int
    local_epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 0.01
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    best_accuracy: Optional[float] = None
    best_f1: Optional[float] = None
    best_auc: Optional[float] = None
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrainingRoundResponse(BaseModel):
    id: str
    round_number: int
    global_accuracy: Optional[float] = None
    global_precision: Optional[float] = None
    global_recall: Optional[float] = None
    global_f1: Optional[float] = None
    global_auc: Optional[float] = None
    global_loss: Optional[float] = None
    participating_clients: int = 0
    total_clients: int = 0
    client_metrics: Dict[str, Any] = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
