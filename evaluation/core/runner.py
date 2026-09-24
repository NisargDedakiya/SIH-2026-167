"""
Generic Evaluation Runner for SatQuery AI.
Orchestrates dataset streaming, model execution, per-sample metric calculation,
error classification, confidence calibration, and result serialization.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.prediction import ModelPrediction
from evaluation.core.sample import BenchmarkSample
from evaluation.core.errors import ErrorCategory
from evaluation.core.aggregation import MetricsAggregator
from evaluation.core.metrics import compute_calibration_metrics


class EvaluationRunner:
    """
    Executes benchmark evaluations and tracks comprehensive per-sample data.
    """

    def __init__(
        self,
        dataset: BenchmarkDataset,
        evaluator: BaseTaskEvaluator,
        model_name: str = "satquery-rs-v1",
        model_version: str = "1.0.0",
        split: str = "test",
        seed: int = 42,
        output_dir: Optional[Path] = None,
    ):
        self.dataset = dataset
        self.evaluator = evaluator
        self.model_name = model_name
        self.model_version = model_version
        self.split = split
        self.seed = seed
        self.output_dir = output_dir or (Path("artifacts") / "evaluation")

    def run(
        self,
        predict_fn: Callable[[BenchmarkSample], ModelPrediction],
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes the evaluation loop across the dataset.
        """
        run_id = f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        started_at = datetime.now(timezone.utc).isoformat()

        # Initialize dataset split and check availability
        self.dataset.load(split=self.split)
        if not self.dataset.is_available:
            return {
                "run_id": run_id,
                "status": "NOT RUN",
                "reason": self.dataset.availability_reason or "Dataset not available on disk",
                "dataset": self.dataset.name,
                "task": self.evaluator.task_name,
                "model": self.model_name,
                "metrics": {},
                "total_samples": 0,
                "latency": {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0},
                "started_at": started_at,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        sample_records: List[Dict[str, Any]] = []
        per_sample_metrics: List[Dict[str, float]] = []
        latencies_ms: List[float] = []
        confidences: List[float] = []
        accuracies: List[float] = []
        errors: List[str] = []

        success_count = 0
        failure_count = 0

        for sample in self.dataset.iter_samples(limit=limit):
            sample_start = time.perf_counter()
            try:
                pred = predict_fn(sample)
                duration_ms = (time.perf_counter() - sample_start) * 1000.0
                if pred.latency_ms <= 0:
                    pred.latency_ms = duration_ms

                metrics, err_cat = self.evaluator.evaluate_sample(sample, pred)

                # Track metrics
                per_sample_metrics.append(metrics)
                latencies_ms.append(pred.latency_ms)
                errors.append(err_cat.value)

                # Determine primary accuracy signal for calibration
                acc_signal = metrics.get("accuracy", metrics.get("exact_match", 1.0 if err_cat == ErrorCategory.NONE else 0.0))
                accuracies.append(float(acc_signal))
                conf = pred.confidence if pred.confidence is not None else 0.85
                confidences.append(float(conf))

                if err_cat == ErrorCategory.NONE:
                    success_count += 1
                else:
                    failure_count += 1

                sample_records.append({
                    "sample_id": sample.sample_id,
                    "task": sample.task,
                    "query": sample.query,
                    "prediction": pred.answer or pred.caption or pred.regions,
                    "reference": sample.reference.get("answer") or sample.reference.get("caption") or sample.reference.get("regions"),
                    "confidence": pred.confidence,
                    "metrics": metrics,
                    "latency_ms": round(pred.latency_ms, 2),
                    "error_category": err_cat.value if err_cat != ErrorCategory.NONE else None,
                })

            except Exception as e:
                failure_count += 1
                errors.append(ErrorCategory.MODEL_FAILURE.value)
                sample_records.append({
                    "sample_id": sample.sample_id,
                    "task": sample.task,
                    "status": "failed",
                    "error": str(e),
                    "error_category": ErrorCategory.MODEL_FAILURE.value,
                })

        completed_at = datetime.now(timezone.utc).isoformat()

        # Compute aggregations
        aggregated_metrics = MetricsAggregator.aggregate_scalar_metrics(per_sample_metrics)
        latency_stats = MetricsAggregator.aggregate_latencies(latencies_ms)
        error_stats = MetricsAggregator.aggregate_errors(errors)
        calibration_stats = compute_calibration_metrics(confidences, accuracies)

        run_manifest = {
            "run_id": run_id,
            "status": "COMPLETED",
            "dataset": self.dataset.name,
            "dataset_version": self.dataset.version,
            "split": self.split,
            "task": self.evaluator.task_name,
            "model": self.model_name,
            "model_version": self.model_version,
            "seed": self.seed,
            "total_samples": len(sample_records),
            "successful_samples": success_count,
            "failed_samples": failure_count,
            "started_at": started_at,
            "completed_at": completed_at,
            "metrics": aggregated_metrics,
            "latency": latency_stats,
            "errors": error_stats,
            "calibration": calibration_stats,
            "sample_predictions": sample_records,
        }

        # Save artifacts to run directory
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        with open(run_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(run_manifest, f, indent=2)

        with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(aggregated_metrics, f, indent=2)

        with open(run_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
            for rec in sample_records:
                f.write(json.dumps(rec) + "\n")

        return run_manifest
