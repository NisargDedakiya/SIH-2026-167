"""
Remote-Sensing Captioning Task Evaluator.
"""

from typing import Dict, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory
from evaluation.core.metrics import compute_bleu, compute_rouge_l, compute_token_f1


class CaptioningTaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates remote-sensing scene description captions.
    """
    task_name = "CAPTIONING"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        pred_cap = prediction.caption or prediction.answer or ""
        ref_cap = sample.ground_truth_caption or sample.ground_truth_answer or ""

        bleu_1 = compute_bleu(pred_cap, ref_cap, max_n=1)
        bleu_4 = compute_bleu(pred_cap, ref_cap, max_n=4)
        rouge_l = compute_rouge_l(pred_cap, ref_cap)
        token_f1 = compute_token_f1(pred_cap, ref_cap)

        metrics = {
            "bleu_1": round(bleu_1, 4),
            "bleu_4": round(bleu_4, 4),
            "rouge_l": round(rouge_l, 4),
            "token_f1": round(token_f1, 4),
        }

        if rouge_l >= 0.35 or bleu_1 >= 0.40:
            err_cat = ErrorCategory.NONE
        else:
            err_cat = ErrorCategory.WRONG_ATTRIBUTE

        return metrics, err_cat
