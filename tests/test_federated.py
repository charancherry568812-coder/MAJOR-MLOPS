"""Federated Learning & FedAvg Simulation Test Suite."""

from federated.simulation import run_federated_simulation


def test_federated_simulation_run():
    config = {
        "use_case": "credit_risk",
        "algorithm": "logistic_regression",
        "strategy": "fedavg",
        "num_rounds": 2,
        "num_clients": 4,
        "run_id": "test-pytest-fl",
    }
    progress_records = []

    def on_progress(round_num, metrics):
        progress_records.append((round_num, metrics))

    result = run_federated_simulation(config, on_progress=on_progress)

    assert result["final_accuracy"] > 0.60
    assert result["total_rounds"] == 2
    assert result["num_clients"] == 4
    assert len(progress_records) == 2
    assert "all_round_metrics" in result
