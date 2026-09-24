"""
Optical + SAR Cross-Modal Task Evaluator.
"""

from typing import Dict, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory
from evaluation.core.metrics import compute_vqa_accuracy, compute_token_f1


class CrossModalTaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates joint Optical and SAR cross-modal fusion, VQA, and grounding.
    """
    task_name = "CROSS_MODAL"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        pred_ans = prediction.answer or ""
        ref_ans = sample.ground_truth_answer or ""

        f1 = compute_token_f1(pred_ans, ref_ans)
        acc = compute_vqa_accuracy(pred_ans, ref_ans)

        # Modality verification score
        modality_verified = 1.0 if ("sar" in pred_ans.lower() or "optical" in pred_ans.lower() or "radar" in pred_ans.lower()) else 0.8

        metrics = {
            "accuracy": round(acc, 4),
            "token_f1": round(f1, 4),
            "modality_alignment": round(modality_verified, 4),
        }

        if acc >= 1.0:
            err_cat = ErrorCategory.NONE
        elif modality_verified < 1.0:
            err_cat = ErrorCategory.MODALITY_REASONING_ERROR
        else:
            err_cat = ErrorCategory.WRONG_ATTRIBUTE

        return metrics, err_cat
