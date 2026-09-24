"""
Comprehensive Metrics Engine for SatQuery AI Benchmark & Evaluation Engine.
Provides standard implementations for VQA, Captioning, Grounding, Change, and Calibration.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# 1. Text & VQA Metrics
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and removing excess whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def compute_exact_match(prediction: str, reference: str) -> float:
    """Case-insensitive exact string match after normalization."""
    return 1.0 if normalize_text(prediction) == normalize_text(reference) else 0.0


def compute_token_f1(prediction: str, reference: str) -> float:
    """Computes harmonic mean of precision and recall between word tokens."""
    pred_tokens = normalize_text(prediction).split()
    ref_tokens = normalize_text(reference).split()

    if not pred_tokens or not ref_tokens:
        return 0.0

    common = set(pred_tokens) & set(ref_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(ref_tokens)

    if precision + recall == 0:
        return 0.0
    return 2.0 * (precision * recall) / (precision + recall)


def compute_vqa_accuracy(prediction: str, reference: str) -> float:
    """Standard VQA relaxed accuracy: 1.0 if EM or Token F1 >= 0.5; 0.0 otherwise."""
    if compute_exact_match(prediction, reference) == 1.0:
        return 1.0
    if compute_token_f1(prediction, reference) >= 0.50:
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# 2. Captioning Metrics (BLEU, ROUGE-L)
# ---------------------------------------------------------------------------
def compute_bleu(prediction: str, reference: str, max_n: int = 4) -> float:
    """Computes simplified cumulative n-gram BLEU score with brevity penalty."""
    pred_tokens = normalize_text(prediction).split()
    ref_tokens = normalize_text(reference).split()

    if not pred_tokens or not ref_tokens:
        return 0.0

    # Brevity penalty
    c = len(pred_tokens)
    r = len(ref_tokens)
    bp = 1.0 if c > r else math.exp(1.0 - (r / max(c, 1)))

    precisions = []
    for n in range(1, min(max_n + 1, len(pred_tokens) + 1)):
        pred_ngrams = [tuple(pred_tokens[i : i + n]) for i in range(len(pred_tokens) - n + 1)]
        ref_ngrams = [tuple(ref_tokens[i : i + n]) for i in range(len(ref_tokens) - n + 1)]

        if not pred_ngrams or not ref_ngrams:
            precisions.append(1e-9)
            continue

        match_count = sum(1 for ng in pred_ngrams if ng in ref_ngrams)
        precisions.append(max(match_count / len(pred_ngrams), 1e-9))

    if not precisions:
        return 0.0

    log_avg = sum(math.log(p) for p in precisions) / len(precisions)
    return float(bp * math.exp(log_avg))


def compute_rouge_l(prediction: str, reference: str) -> float:
    """Computes Longest Common Subsequence (LCS) based ROUGE-L score."""
    p_tokens = normalize_text(prediction).split()
    r_tokens = normalize_text(reference).split()

    m, n = len(p_tokens), len(r_tokens)
    if m == 0 or n == 0:
        return 0.0

    # LCS DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if p_tokens[i] == r_tokens[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])

    lcs_len = dp[m][n]
    prec = lcs_len / m
    rec = lcs_len / n
    if prec + rec == 0:
        return 0.0
    return float((2.0 * prec * rec) / (prec + rec))


# ---------------------------------------------------------------------------
# 3. Grounding & Spatial Metrics (IoU, Recall@threshold)
# ---------------------------------------------------------------------------
def compute_box_iou(box1: List[float], box2: List[float]) -> float:
    """
    Computes Intersection-over-Union for bounding boxes in [ymin, xmin, ymax, xmax] format.
    """
    ymin1, xmin1, ymax1, xmax1 = box1
    ymin2, xmin2, ymax2, xmax2 = box2

    inter_ymin = max(ymin1, ymin2)
    inter_xmin = max(xmin1, xmin2)
    inter_ymax = min(ymax1, ymax2)
    inter_xmax = min(xmax1, xmax2)

    inter_w = max(0.0, inter_xmax - inter_xmin)
    inter_h = max(0.0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h

    area1 = max(0.0, (xmax1 - xmin1) * (ymax1 - ymin1))
    area2 = max(0.0, (xmax2 - xmin2) * (ymax2 - ymin2))
    union_area = area1 + area2 - inter_area

    if union_area <= 0.0:
        return 0.0
    return float(inter_area / union_area)


def compute_grounding_metrics(
    pred_boxes: List[List[float]],
    gt_boxes: List[List[float]],
    threshold: float = 0.50
) -> Dict[str, float]:
    """
    Computes mean IoU, Recall@threshold, and Precision@threshold.
    """
    if not gt_boxes:
        return {"mean_iou": 0.0, "recall": 0.0, "precision": 0.0}
    if not pred_boxes:
        return {"mean_iou": 0.0, "recall": 0.0, "precision": 0.0}

    matched_gt = set()
    ious = []

    for p_box in pred_boxes:
        best_iou = 0.0
        best_gt_idx = -1
        for g_idx, g_box in enumerate(gt_boxes):
            iou = compute_box_iou(p_box, g_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = g_idx

        ious.append(best_iou)
        if best_iou >= threshold and best_gt_idx != -1:
            matched_gt.add(best_gt_idx)

    mean_iou = float(np.mean(ious)) if ious else 0.0
    recall = len(matched_gt) / len(gt_boxes)
    precision = len(matched_gt) / len(pred_boxes) if pred_boxes else 0.0

    return {
        "mean_iou": round(mean_iou, 4),
        f"recall@{threshold}": round(recall, 4),
        f"precision@{threshold}": round(precision, 4),
    }


# ---------------------------------------------------------------------------
# 4. Change Detection Binary Mask Metrics
# ---------------------------------------------------------------------------
def compute_mask_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray) -> Dict[str, float]:
    """Computes binary IoU, Precision, Recall, and F1 on 2D change masks."""
    p = (pred_mask > 0).astype(bool)
    g = (gt_mask > 0).astype(bool)

    tp = np.logical_and(p, g).sum()
    fp = np.logical_and(p, np.logical_not(g)).sum()
    fn = np.logical_and(np.logical_not(p), g).sum()

    intersection = tp
    union = tp + fp + fn

    iou = float(intersection / union) if union > 0 else 1.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float((2 * precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "iou": round(iou, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


# ---------------------------------------------------------------------------
# 5. Confidence Calibration (ECE, Brier Score, Reliability Bins)
# ---------------------------------------------------------------------------
def compute_calibration_metrics(
    confidences: List[float],
    accuracies: List[float],
    n_bins: int = 5
) -> Dict[str, Any]:
    """
    Computes Expected Calibration Error (ECE), Brier Score, and reliability bins.
    """
    if not confidences or not accuracies:
        return {"ece": 0.0, "brier_score": 0.0, "bins": []}

    confs = np.array(confidences)
    accs = np.array(accuracies)

    # Brier Score: Mean Squared Error between confidence and binary correctness
    brier_score = float(np.mean((confs - accs) ** 2))

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    bin_data = []
    ece = 0.0
    total_samples = len(confs)

    for i in range(n_bins):
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        in_bin = (confs >= low) & (confs <= high if i == n_bins - 1 else confs < high)
        count = int(in_bin.sum())

        if count > 0:
            bin_acc = float(accs[in_bin].mean())
            bin_conf = float(confs[in_bin].mean())
            ece += (count / total_samples) * abs(bin_acc - bin_conf)
            bin_data.append({
                "range": f"{low:.1f}–{high:.1f}",
                "count": count,
                "confidence": round(bin_conf, 3),
                "accuracy": round(bin_acc, 3),
                "error": round(abs(bin_acc - bin_conf), 3),
            })
        else:
            bin_data.append({
                "range": f"{low:.1f}–{high:.1f}",
                "count": 0,
                "confidence": round((low + high) / 2.0, 3),
                "accuracy": 0.0,
                "error": 0.0,
            })

    return {
        "ece": round(float(ece), 4),
        "brier_score": round(brier_score, 4),
        "bins": bin_data,
    }
