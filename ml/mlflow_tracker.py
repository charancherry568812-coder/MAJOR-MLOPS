"""MLflow experiment tracking and model registry utility for FedBank MLOps.

Supports both local tracking (file-based or sqlite) and remote MLflow tracking servers.
Includes graceful fallback if MLflow server is temporarily offline.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MLflowTracker:
    """Enterprise MLflow tracking and Model Registry client."""

    def __init__(self, tracking_uri: Optional[str] = None):
        self.tracking_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
        self._mlflow = None
        self._initialized = False
        self._init_mlflow()

    def _init_mlflow(self):
        try:
            import mlflow
            self._mlflow = mlflow
            # If tracking_uri is a local relative path, ensure directory exists
            if not self.tracking_uri.startswith("http"):
                Path(self.tracking_uri).mkdir(parents=True, exist_ok=True)
            self._mlflow.set_tracking_uri(self.tracking_uri)
            self._initialized = True
            logger.info(f"MLflow tracker initialized with URI: {self.tracking_uri}")
        except Exception as e:
            logger.warning(f"MLflow initialization deferred: {e}")
            self._initialized = False

    @property
    def is_available(self) -> bool:
        return self._initialized and self._mlflow is not None

    def start_run(self, experiment_name: str, run_name: Optional[str] = None) -> Optional[str]:
        """Start a new MLflow run under an experiment."""
        if not self.is_available:
            return None
        try:
            self._mlflow.set_experiment(experiment_name)
            run = self._mlflow.start_run(run_name=run_name)
            return run.info.run_id
        except Exception as e:
            logger.warning(f"Failed to start MLflow run: {e}")
            return None

    def log_params(self, params: Dict[str, Any]):
        """Log training parameters or hyperparameters."""
        if not self.is_available:
            return
        try:
            self._mlflow.log_params(params)
        except Exception as e:
            logger.warning(f"Failed to log params to MLflow: {e}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log scalar metrics at an optional FL round or epoch step."""
        if not self.is_available:
            return
        try:
            # Filter out non-numeric metrics
            numeric_metrics = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
            self._mlflow.log_metrics(numeric_metrics, step=step)
        except Exception as e:
            logger.warning(f"Failed to log metrics to MLflow: {e}")

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log a local file or model as an artifact."""
        if not self.is_available or not os.path.exists(local_path):
            return
        try:
            self._mlflow.log_artifact(local_path, artifact_path=artifact_path)
        except Exception as e:
            logger.warning(f"Failed to log artifact to MLflow: {e}")

    def log_dict_as_json(self, data: dict, filename: str):
        """Save a dictionary as a JSON artifact in the active run."""
        if not self.is_available:
            return
        try:
            self._mlflow.log_dict(data, filename)
        except Exception as e:
            logger.warning(f"Failed to log dict to MLflow: {e}")

    def end_run(self, status: str = "FINISHED"):
        """End active MLflow run."""
        if not self.is_available:
            return
        try:
            self._mlflow.end_run(status=status)
        except Exception as e:
            logger.warning(f"Failed to end MLflow run: {e}")

    def register_model(
        self,
        model_name: str,
        model_artifact_uri: str,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ) -> Optional[str]:
        """Register a model in the MLflow Model Registry."""
        if not self.is_available:
            return None
        try:
            from mlflow.tracking import MlflowClient
            client = MlflowClient(self.tracking_uri)

            # Create registered model if not exists
            try:
                client.create_registered_model(model_name, tags=tags, description=description)
            except Exception:
                pass  # already exists

            # Create model version
            mv = client.create_model_version(
                name=model_name,
                source=model_artifact_uri,
                run_id=self._mlflow.active_run().info.run_id if self._mlflow.active_run() else None,
                tags=tags,
                description=description,
            )
            return str(mv.version)
        except Exception as e:
            logger.warning(f"Model registration in MLflow registry failed: {e}")
            return None

    def transition_stage(self, model_name: str, version: str, stage: str):
        """Transition model version stage (e.g. Staging, Production, Archived)."""
        if not self.is_available:
            return
        try:
            from mlflow.tracking import MlflowClient
            client = MlflowClient(self.tracking_uri)
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=(stage.lower() == "production"),
            )
        except Exception as e:
            logger.warning(f"Failed to transition MLflow model stage: {e}")


# Singleton instance
mlflow_tracker = MLflowTracker()
