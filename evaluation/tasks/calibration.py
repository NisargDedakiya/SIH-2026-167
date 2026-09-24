"""
Confidence Calibration Evaluator for SatQuery AI (Part 23).
Calculates Expected Calibration Error (ECE), Brier Score, and confidence vs accuracy binning.
"""

from typing import Any, Dict, List
from evaluation.core.metrics import compute_calibration_metrics


class CalibrationEvaluator:
    """
    Evaluates confidence calibration across benchmark predictions.
    """

    @staticmethod
    def evaluate(confidences: List[float], correctness_signals: List[float], n_bins: int = 5) -> Dict[str, Any]:
        """
        Computes ECE, Brier Score, and 5-bin reliability statistics.
        """
        metrics = compute_calibration_metrics(confidences, correctness_signals, n_bins=n_bins)
        
        # Categorize calibration quality
        ece = metrics["ece"]
        if ece < 0.10:
            quality = "EXCELLENT_CALIBRATION"
        elif ece < 0.20:
            quality = "MODERATE_CALIBRATION"
        else:
            quality = "MISCALIBRATED_OVERCONFIDENT"

        metrics["calibration_quality"] = quality
        return metrics
