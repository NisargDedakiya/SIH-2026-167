"""
VRSBench Remote-Sensing Evaluation Metrics.
Computes exact match, token F1, and relaxed accuracy for remote-sensing VQA and captioning.
"""

import re
from typing import Any, Dict, List


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.,;!]+$", "", text)
    return text


def compute_exact_match(prediction: str, reference: str) -> float:
    return 1.0 if normalize_text(prediction) == normalize_text(reference) else 0.0


def compute_token_f1(prediction: str, reference: str) -> float:
    pred_tokens = set(normalize_text(prediction).split())
    ref_tokens = set(normalize_text(reference).split())

    if not pred_tokens or not ref_tokens:
        return 1.0 if pred_tokens == ref_tokens else 0.0

    common = pred_tokens.intersection(ref_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def evaluate_predictions(predictions: List[str], references: List[str]) -> Dict[str, float]:
    assert len(predictions) == len(references), "Predictions and references must have identical length."
    if not predictions:
        return {"exact_match": 0.0, "token_f1": 0.0, "accuracy": 0.0}

    em_scores = [compute_exact_match(p, r) for p, r in zip(predictions, references)]
    f1_scores = [compute_token_f1(p, r) for p, r in zip(predictions, references)]

    # Semantic accuracy: exact match OR token F1 >= 0.5
    relaxed_acc = [1.0 if (em == 1.0 or f1 >= 0.5) else 0.0 for em, f1 in zip(em_scores, f1_scores)]

    return {
        "exact_match": float(sum(em_scores) / len(em_scores)),
        "token_f1": float(sum(f1_scores) / len(f1_scores)),
        "accuracy": float(sum(relaxed_acc) / len(relaxed_acc)),
    }
