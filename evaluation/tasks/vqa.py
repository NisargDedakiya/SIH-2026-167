"""
Remote-Sensing VQA Task Evaluator.
"""

from typing import Dict, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory, classify_vqa_error
from evaluation.core.metrics import compute_exact_match, compute_token_f1, compute_vqa_accuracy


class VQATaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates Visual Question Answering predictions against ground truth references.
    """
    task_name = "VQA"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
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
            err_cat = classify_vqa_error(
                prediction=pred_ans,
                reference=ref_ans,
                confidence=prediction.confidence,
                query=sample.query
            )

        return metrics, err_cat
