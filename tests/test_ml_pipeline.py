"""Machine Learning Pipeline & Model Training Test Suite."""

import os
import pandas as pd
import numpy as np
from ml.pipeline import Preprocessor, create_model, evaluate_model, train_model


def test_preprocessor_fit_transform():
    df = pd.read_csv("dataset_storage/bank-001_customers.csv")
    preprocessor = Preprocessor("credit_risk")
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.fit_transform(df)

    assert X_train.shape[0] > 0
    assert X_val.shape[0] > 0
    assert X_test.shape[0] > 0
    assert len(preprocessor.feature_names) == 11
    assert not np.isnan(X_train).any()


def test_model_training_and_metrics():
    df = pd.read_csv("dataset_storage/bank-001_customers.csv")
    preprocessor = Preprocessor("credit_risk")
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.fit_transform(df)

    model = create_model("credit_risk", "random_forest")
    metrics = model.train(X_train, y_train, X_val, y_val)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert metrics["accuracy"] >= 0.70

    preds = model.predict(X_test)
    assert len(preds) == len(y_test)
