"""Flower Federated Learning Server for FedBank MLOps.

Implements FedAvg with custom metrics aggregation for multiple banking nodes.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.mlflow_tracker import mlflow_tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [FedServer] %(message)s")
logger = logging.getLogger("FlowerServer")


def weighted_average(metrics: List[Tuple[int, Dict[str, float]]]) -> Dict[str, float]:
    """Aggregate evaluation metrics from all participating bank clients."""
    accuracies = [num_examples * m.get("accuracy", 0.0) for num_examples, m in metrics]
    losses = [num_examples * m.get("loss", 0.0) for num_examples, m in metrics]
    f1s = [num_examples * m.get("f1", 0.0) for num_examples, m in metrics]
    total_examples = sum(num_examples for num_examples, _ in metrics)

    if total_examples == 0:
        return {"accuracy": 0.0, "loss": 0.0, "f1": 0.0}

    agg_acc = round(float(sum(accuracies) / total_examples), 4)
    agg_loss = round(float(sum(losses) / total_examples), 4)
    agg_f1 = round(float(sum(f1s) / total_examples), 4)

    logger.info(f"Aggregated round metrics — Accuracy: {agg_acc:.4f}, Loss: {agg_loss:.4f}, F1: {agg_f1:.4f}")
    return {"accuracy": agg_acc, "loss": agg_loss, "f1": agg_f1}


def start_flower_server(
    server_address: str = "0.0.0.0:8080",
    num_rounds: int = 5,
    min_clients: int = 4,
    experiment_name: str = "FedBank-FL-Global",
) -> Dict[str, any]:
    """Start central Flower Federated Learning server."""
    try:
        import flwr as fl
        from flwr.server.strategy import FedAvg
    except ImportError:
        logger.error("Flower (flwr) library not installed. Use simulation mode instead.")
        return {"success": False, "error": "Flower library not installed"}

    logger.info(f"Starting Flower Federated Server at {server_address} for {num_rounds} rounds with {min_clients} banks...")

    # Start MLflow run for tracking global FL execution
    run_id = mlflow_tracker.start_run(experiment_name=experiment_name, run_name=f"FL-Rounds-{num_rounds}")
    if run_id:
        mlflow_tracker.log_params({
            "strategy": "FedAvg",
            "num_rounds": num_rounds,
            "min_clients": min_clients,
            "server_address": server_address,
        })

    # Strategy: FedAvg with custom metrics aggregation
    strategy = FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        evaluate_metrics_aggregation_fn=weighted_average,
        fit_metrics_aggregation_fn=weighted_average,
    )

    try:
        history = fl.server.start_server(
            server_address=server_address,
            config=fl.server.ServerConfig(num_rounds=num_rounds),
            strategy=strategy,
        )
        logger.info("Flower federated learning session completed successfully.")

        if run_id:
            mlflow_tracker.end_run(status="FINISHED")

        return {"success": True, "history": str(history)}
    except Exception as e:
        logger.error(f"Error running Flower server: {e}")
        if run_id:
            mlflow_tracker.end_run(status="FAILED")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start FedBank Flower Server")
    parser.add_argument("--address", default="0.0.0.0:8080", help="Server listen host:port")
    parser.add_argument("--rounds", type=int, default=5, help="Number of FL rounds")
    parser.add_argument("--min-clients", type=int, default=4, help="Minimum clients required")
    parser.add_argument("--experiment", default="FedBank-FL-Global", help="MLflow experiment name")
    args = parser.parse_args()

    start_flower_server(
        server_address=args.address,
        num_rounds=args.rounds,
        min_clients=args.min_clients,
        experiment_name=args.experiment,
    )
