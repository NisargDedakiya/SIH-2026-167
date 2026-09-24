"""
VRSBench Evaluation Runner.
Executes inference on benchmark items and computes quantitative metrics.
"""

import time
from typing import Any, Callable, Dict, List
from evaluation.vrsbench.loader import VRSBenchLoader
from evaluation.vrsbench.metrics import evaluate_predictions


class VRSBenchRunner:
    """
    Executes benchmark evaluations against a model inference function.
    """

    @classmethod
    def run_evaluation(
        cls,
        model_fn: Callable[[Any, str], str],
        model_name: str = "generic_model"
    ) -> Dict[str, Any]:
        eval_items = VRSBenchLoader.load_evaluation_set()
        predictions: List[str] = []
        references: List[str] = []
        latencies: List[float] = []

        for item in eval_items:
            t0 = time.time()
            pred = model_fn(item["image"], item["query"])
            lat = time.time() - t0
            latencies.append(lat)
            predictions.append(pred)
            references.append(item["reference"])

        metrics = evaluate_predictions(predictions, references)
        metrics["mean_latency_ms"] = float(sum(latencies) / len(latencies) * 1000)
        metrics["total_samples"] = len(eval_items)
        metrics["model_name"] = model_name

        results = []
        for item, pred in zip(eval_items, predictions):
            results.append({
                "id": item["id"],
                "category": item["category"],
                "query": item["query"],
                "reference": item["reference"],
                "prediction": pred,
            })

        return {
            "metrics": metrics,
            "results": results,
        }
