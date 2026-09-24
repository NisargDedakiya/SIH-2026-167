"""
RSVQA Evaluation Runner.
Computes accuracy on presence and comparison queries against ground truth.
"""

import time
from typing import Any, Callable, Dict, List
from evaluation.rsvqa.loader import RSVQADataLoader
from evaluation.vrsbench.metrics import normalize_text


class RSVQARunner:
    """
    Evaluates remote-sensing presence/comparison VQA queries.
    """

    @classmethod
    def run_evaluation(
        cls,
        model_fn: Callable[[Any, str], str],
        model_name: str = "generic_model"
    ) -> Dict[str, Any]:
        eval_items = RSVQADataLoader.load_evaluation_set()
        correct = 0
        latencies = []
        results = []

        for item in eval_items:
            t0 = time.time()
            pred = model_fn(item["image"], item["query"])
            lat = time.time() - t0
            latencies.append(lat)

            norm_pred = normalize_text(pred)
            norm_ref = normalize_text(item["reference"])

            is_correct = (norm_ref in norm_pred) or (norm_pred == norm_ref)
            if is_correct:
                correct += 1

            results.append({
                "id": item["id"],
                "type": item["type"],
                "query": item["query"],
                "reference": item["reference"],
                "prediction": pred,
                "is_correct": is_correct,
            })

        acc = float(correct / max(len(eval_items), 1))
        return {
            "metrics": {
                "accuracy": acc,
                "correct_samples": correct,
                "total_samples": len(eval_items),
                "mean_latency_ms": float(sum(latencies) / len(latencies) * 1000),
                "model_name": model_name,
            },
            "results": results,
        }
