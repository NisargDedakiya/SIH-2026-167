"""
Remote-Sensing Visual Grounding Task Evaluator.
"""

from typing import Dict, List, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory
from evaluation.core.metrics import compute_grounding_metrics


class GroundingTaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates visual grounding bounding boxes / spatial coordinates.
    """
    task_name = "GROUNDING"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        pred_boxes: List[List[float]] = []
        for r in prediction.regions:
            b = r.get("box_2d") or r.get("bbox") or [r.get("ymin", 0), r.get("xmin", 0), r.get("ymax", 0), r.get("xmax", 0)]
            if len(b) == 4:
                pred_boxes.append([float(x) for x in b])

        gt_boxes: List[List[float]] = []
        for r in sample.ground_truth_regions:
            b = r.get("box_2d") or r.get("bbox") or [r.get("ymin", 0), r.get("xmin", 0), r.get("ymax", 0), r.get("xmax", 0)]
            if len(b) == 4:
                gt_boxes.append([float(x) for x in b])

        metrics = compute_grounding_metrics(pred_boxes, gt_boxes, threshold=0.50)

        if metrics.get("recall@0.5", 0.0) >= 0.50:
            err_cat = ErrorCategory.NONE
        elif not pred_boxes:
            err_cat = ErrorCategory.INSUFFICIENT_EVIDENCE
        else:
            err_cat = ErrorCategory.WRONG_LOCATION

        return metrics, err_cat
