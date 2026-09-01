"""Flower Bank Client Node for FedBank MLOps.

Runs locally at a member bank/branch.
Loads the bank's private dataset, performs local training, evaluates locally,
and sends ONLY parameter updates and evaluation metrics to the central Flower server.
Raw banking customer data NEVER leaves the local machine/container.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.pipeline import Preprocessor, create_model, evaluate_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [FedClient] %(message)s")
logger = logging.getLogger("FlowerClient")


class BankFlowerClient:
    """Flower NumPyClient implementation for a banking node."""

    def __init__(
        self,
        bank_code: str,
        dataset_path: str,
        use_case: str = "credit_risk",
        algorithm: str = "logistic_regression",
    ):
        self.bank_code = bank_code
        self.dataset_path = dataset_path
        self.use_case = use_case
        self.algorithm = algorithm

        logger.info(f"Initializing {bank_code} client node for {use_case}...")
        self.preprocessor = Preprocessor(use_case)
        self._load_and_preprocess()

        # Initialize local model
        self.model = create_model(use_case, algorithm)
        self.model._feature_names = self.preprocessor.feature_names
        # Initial fit on 10 samples to initialize model shapes
        self.model.model.fit(self.X_train[:10], self.y_train[:10])

    def _load_and_preprocess(self):
        """Load local dataset from disk and preprocess into train, validation, test splits."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Local bank dataset not found at {self.dataset_path}")

        df = pd.read_csv(self.dataset_path)
        logger.info(f"Loaded private dataset for {self.bank_code}: {len(df)} records")
        (
            self.X_train,
            self.X_val,
            self.X_test,
            self.y_train,
            self.y_val,
            self.y_test,
        ) = self.preprocessor.fit_transform(df)

    def get_parameters(self, config: Dict[str, any]) -> List[np.ndarray]:
        """Return model parameters as list of NumPy arrays."""
        if hasattr(self.model.model, "coef_"):
            return [self.model.model.coef_.copy(), self.model.model.intercept_.copy()]
        # Fallback for tree-based representations
        return [np.zeros((1,))]

    def set_parameters(self, parameters: List[np.ndarray]):
        """Set local model parameters received from aggregated global model."""
        if hasattr(self.model.model, "coef_") and len(parameters) >= 2:
            self.model.model.coef_ = parameters[0].copy()
            self.model.model.intercept_ = parameters[1].copy()

    def fit(self, parameters: List[np.ndarray], config: Dict[str, any]) -> Tuple[List[np.ndarray], int, Dict[str, float]]:
        """Train local model using local customer dataset."""
        logger.info(f"[{self.bank_code}] Starting local training round...")
        self.set_parameters(parameters)

        # Train on private local data
        self.model.model.fit(self.X_train, self.y_train)

        # Evaluate on local validation split
        y_val_pred = self.model.model.predict(self.X_val)
        y_val_proba = self.model.model.predict_proba(self.X_val)[:, 1] if hasattr(self.model.model, "predict_proba") else None
        metrics = evaluate_model(self.y_val, y_val_pred, y_val_proba)

        logger.info(f"[{self.bank_code}] Local round complete — Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1']:.4f}")

        return (
            self.get_parameters(config),
            len(self.X_train),
            {"accuracy": metrics["accuracy"], "loss": 1.0 - metrics["accuracy"], "f1": metrics["f1"]},
        )

    def evaluate(self, parameters: List[np.ndarray], config: Dict[str, any]) -> Tuple[float, int, Dict[str, float]]:
        """Evaluate received global parameters on local test dataset."""
        self.set_parameters(parameters)
        y_test_pred = self.model.model.predict(self.X_test)
        y_test_proba = self.model.model.predict_proba(self.X_test)[:, 1] if hasattr(self.model.model, "predict_proba") else None
        metrics = evaluate_model(self.y_test, y_test_pred, y_test_proba)

        loss = float(1.0 - metrics["accuracy"])
        return loss, len(self.X_test), {"accuracy": metrics["accuracy"], "loss": loss, "f1": metrics["f1"]}


def start_flower_client(
    server_address: str = "127.0.0.1:8080",
    bank_code: str = "BANK-001",
    dataset_path: Optional[str] = None,
    use_case: str = "credit_risk",
    algorithm: str = "logistic_regression",
):
    """Start a Flower client node for a bank."""
    try:
        import flwr as fl
    except ImportError:
        logger.error("Flower library not found. Please install flwr.")
        return

    # Locate dataset path if not specified
    if not dataset_path:
        default_dir = os.path.join(os.path.dirname(__file__), "..", "dataset_storage")
        filename = f"{bank_code.lower()}_customers.csv"
        dataset_path = os.path.join(default_dir, filename)

    if not os.path.exists(dataset_path):
        # Generate synthetic data if file doesn't exist
        from scripts.generate_data import generate_all_datasets
        generate_all_datasets(os.path.dirname(dataset_path))

    client = BankFlowerClient(
        bank_code=bank_code,
        dataset_path=dataset_path,
        use_case=use_case,
        algorithm=algorithm,
    )

    class FlowerBridge(fl.client.NumPyClient):
        def get_parameters(self, config):
            return client.get_parameters(config)

        def fit(self, parameters, config):
            return client.fit(parameters, config)

        def evaluate(self, parameters, config):
            return client.evaluate(parameters, config)

    logger.info(f"Connecting {bank_code} client node to Flower Server at {server_address}...")
    fl.client.start_client(server_address=server_address, client=FlowerBridge().to_client())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start FedBank Flower Client Node")
    parser.add_argument("--server", default="127.0.0.1:8080", help="Flower server address host:port")
    parser.add_argument("--bank", default="BANK-001", help="Bank identifier (e.g. BANK-001, BANK-002)")
    parser.add_argument("--dataset", default=None, help="Path to local dataset CSV")
    parser.add_argument("--use-case", default="credit_risk", help="Use case name")
    parser.add_argument("--algorithm", default="logistic_regression", help="Model algorithm")
    args = parser.parse_args()

    start_flower_client(
        server_address=args.server,
        bank_code=args.bank,
        dataset_path=args.dataset,
        use_case=args.use_case,
        algorithm=args.algorithm,
    )
