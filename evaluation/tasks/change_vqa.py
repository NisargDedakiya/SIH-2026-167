"""
Bi-Temporal Change VQA Task Evaluator.
"""

from typing import Dict, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory
from evaluation.core.metrics import compute_exact_match, compute_token_f1, compute_vqa_accuracy


class ChangeVQATaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates Bi-Temporal Change Visual Question Answering.
    Verifies that both T1 and T2 images were evaluated.
    """
    task_name = "CHANGE_VQA"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        # Assert bi-temporal inputs
        if sample.t1_image is None or sample.t2_image is None:
            return {"accuracy": 0.0, "token_f1": 0.0}, ErrorCategory.PAIR_VALIDATION_FAILURE

        pred_ans = prediction.answer or ""
        ref_ans = sample.ground_truth_answer or ""

        em = compute_exact_match(pred_ans, ref_ans)
        f1 = compute_token_f1(pred_ans, ref_ans)
        acc = compute_vqa_accuracy(pred_ans, ref_ans)

        metrics = {
            "exact_match": round(em, 4),
            "token_f1": round(f1, 4),
            "accuracy": round(acc, 4),
        }

        if acc >= 1.0:
            err_cat = ErrorCategory.NONE
        else:
            err_cat = ErrorCategory.TEMPORAL_REASONING_ERROR

        return metrics, err_cat
