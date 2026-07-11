"""Airflow DAG for optimal advertising pressure calculation."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from airflow.decorators import dag, task

from db import queries
from db.repository import DataRepository
from services import extract as extract_service
from services import predict as predict_service
from services import preprocessing as preprocessing_service
from services import profit as profit_service
from services import save as save_service
from services.settings import Settings

SETTINGS = Settings()


@dag(
    dag_id="optimal_advertising_pressure_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ozon", "advertising", "optimization"],
)
def optimal_advertising_pressure_dag() -> None:
    """Calculate optimal advertising pressure for Ozon products."""

    @task(task_id="extract_categories")
    def extract_categories_task() -> str:
        repository = DataRepository()
        frame = extract_service.extract_categories(
            repository,
            queries.DEFAULT_CUSTOMER_KEY,
        )
        return _write_frame(frame, "categories")

    @task(task_id="extract_advertising")
    def extract_advertising_task() -> str:
        repository = DataRepository()
        frame = extract_service.extract_advertising(
            repository,
            queries.DEFAULT_CUSTOMER_KEY,
        )
        return _write_frame(frame, "advertising")

    @task(task_id="extract_prices")
    def extract_prices_task() -> str:
        repository = DataRepository()
        frame = extract_service.extract_prices(repository, queries.DEFAULT_CUSTOMER_KEY)
        return _write_frame(frame, "prices")

    @task(task_id="extract_self_cost")
    def extract_self_cost_task() -> str:
        repository = DataRepository()
        frame = extract_service.extract_self_cost(
            repository,
            queries.DEFAULT_CUSTOMER_KEY,
        )
        return _write_frame(frame, "self_cost")

    @task(task_id="extract_sales")
    def extract_sales_task() -> str:
        repository = DataRepository()
        frame = extract_service.extract_sales(repository, queries.DEFAULT_CUSTOMER_KEY)
        return _write_frame(frame, "sales")

    @task(task_id="build_feature_mart")
    def build_feature_mart_task(
        sales_path: str,
        categories_path: str,
        advertising_path: str,
        prices_path: str,
        self_cost_path: str,
    ) -> str:
        frame = preprocessing_service.build_feature_mart(
            sales=_read_frame(sales_path),
            categories=_read_frame(categories_path),
            advertising=_read_frame(advertising_path),
            prices=_read_frame(prices_path),
            self_cost=_read_frame(self_cost_path),
        )
        return _write_frame(frame, "feature_mart")

    @task(task_id="aggregate_daily_metrics")
    def aggregate_daily_metrics_task(feature_mart_path: str) -> str:
        frame = preprocessing_service.aggregate_daily_metrics(
            _read_frame(feature_mart_path),
        )
        return _write_frame(frame, "daily_metrics")

    @task(task_id="calculate_history_features")
    def calculate_history_features_task(daily_metrics_path: str) -> str:
        frame = preprocessing_service.calculate_history_features(
            _read_frame(daily_metrics_path),
        )
        return _write_frame(frame, "history_features")

    @task(task_id="predict_metrics")
    def predict_metrics_task(history_features_path: str) -> str:
        frame = predict_service.predict_metrics(_read_frame(history_features_path))
        return _write_frame(frame, "predictions")

    @task(task_id="calculate_profit")
    def calculate_profit_task(predictions_path: str) -> str:
        frame = profit_service.calculate_profit(_read_frame(predictions_path))
        return _write_frame(frame, "profits")

    @task(task_id="select_optimal_pressure")
    def select_optimal_pressure_task(profits_path: str) -> str:
        frame = profit_service.select_best_pressure(_read_frame(profits_path))
        return _write_frame(frame, "optimal_pressure")

    @task(task_id="save_results")
    def save_results_task(optimal_pressure_path: str) -> str:
        saved = save_service.save_results(_read_frame(optimal_pressure_path))
        return _write_frame(saved, "saved_results")

    categories_path = extract_categories_task()
    advertising_path = extract_advertising_task()
    prices_path = extract_prices_task()
    self_cost_path = extract_self_cost_task()
    sales_path = extract_sales_task()

    feature_mart_path = build_feature_mart_task(
        sales_path,
        categories_path,
        advertising_path,
        prices_path,
        self_cost_path,
    )
    daily_metrics_path = aggregate_daily_metrics_task(feature_mart_path)
    history_features_path = calculate_history_features_task(daily_metrics_path)
    predictions_path = predict_metrics_task(history_features_path)
    profits_path = calculate_profit_task(predictions_path)
    optimal_pressure_path = select_optimal_pressure_task(profits_path)
    save_results_task(optimal_pressure_path)

    categories_path >> advertising_path >> prices_path >> self_cost_path >> sales_path


def _write_frame(frame: pd.DataFrame, name: str) -> str:
    """Write a task artifact and return its path."""
    path = _artifact_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return str(path)


def _read_frame(path: str) -> pd.DataFrame:
    """Read a task artifact."""
    return pd.read_csv(path)


def _artifact_path(name: str) -> Path:
    """Build a deterministic artifact path for the current DAG run."""
    run_id = os.getenv("AIRFLOW_CTX_DAG_RUN_ID", "local")
    safe_run_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", run_id)
    return SETTINGS.artifact_dir / safe_run_id / f"{name}.csv"


optimal_advertising_pressure_dag()
