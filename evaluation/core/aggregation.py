"""
Metrics and Latency Aggregation Engine for SatQuery AI.
"""

from typing import Any, Dict, List
import numpy as np


class MetricsAggregator:
    """
    Aggregates per-sample metrics, latencies, and error statistics.
    """

    @staticmethod
    def aggregate_scalar_metrics(per_sample_metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """Averages all scalar metric values across samples."""
        if not per_sample_metrics:
            return {}

        keys = set().union(*per_sample_metrics)
        aggregated = {}

        for k in keys:
            vals = [m[k] for m in per_sample_metrics if k in m and m[k] is not None]
            if vals:
                aggregated[k] = round(float(np.mean(vals)), 4)
            else:
                aggregated[k] = 0.0

        return aggregated

    @staticmethod
    def aggregate_latencies(latencies_ms: List[float]) -> Dict[str, float]:
        """Calculates latency distribution statistics."""
        if not latencies_ms:
            return {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}

        arr = np.array(latencies_ms)
        return {
            "mean_ms": round(float(np.mean(arr)), 2),
            "median_ms": round(float(np.median(arr)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2),
            "min_ms": round(float(np.min(arr)), 2),
            "max_ms": round(float(np.max(arr)), 2),
        }

    @staticmethod
    def aggregate_errors(error_categories: List[str]) -> Dict[str, Any]:
        """Calculates error counts and percentage distribution."""
        total = len(error_categories)
        if total == 0:
            return {"total_errors": 0, "breakdown": {}}

        counts: Dict[str, int] = {}
        for err in error_categories:
            if err and err != "NONE":
                counts[err] = counts.get(err, 0) + 1

        total_err_count = sum(counts.values())
        breakdown = {}
        for err, cnt in counts.items():
            breakdown[err] = {
                "count": cnt,
                "percentage": round((cnt / total) * 100.0, 1),
            }

        return {
            "total_samples": total,
            "total_errors": total_err_count,
            "error_rate": round((total_err_count / total) * 100.0, 2) if total > 0 else 0.0,
            "breakdown": breakdown,
        }
