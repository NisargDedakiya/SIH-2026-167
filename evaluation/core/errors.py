"""
Standard Error Taxonomy for SatQuery AI Benchmark & Evaluation Engine (Part 27).
Forbids vague error classes in favor of rigorous root-cause categorization.
"""

from enum import Enum
from typing import Optional


class ErrorCategory(str, Enum):
    # Data & Ingestion Errors
    INPUT_FAILURE = "INPUT_FAILURE"
    PAIR_VALIDATION_FAILURE = "PAIR_VALIDATION_FAILURE"
    ALIGNMENT_FAILURE = "ALIGNMENT_FAILURE"

    # Agent & Orchestration Errors
    WRONG_INTENT = "WRONG_INTENT"
    WRONG_TOOL = "WRONG_TOOL"

    # Vision-Language Semantic Errors
    WRONG_OBJECT = "WRONG_OBJECT"
    WRONG_LOCATION = "WRONG_LOCATION"
    WRONG_COUNT = "WRONG_COUNT"
    WRONG_ATTRIBUTE = "WRONG_ATTRIBUTE"

    # Multimodal & Temporal Reasoning Errors
    TEMPORAL_REASONING_ERROR = "TEMPORAL_REASONING_ERROR"
    MODALITY_REASONING_ERROR = "MODALITY_REASONING_ERROR"

    # Reliability & Safety Errors
    HALLUCINATION = "HALLUCINATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    OVERCONFIDENT_ERROR = "OVERCONFIDENT_ERROR"

    # Execution & System Errors
    MODEL_FAILURE = "MODEL_FAILURE"
    TIMEOUT = "TIMEOUT"
    NONE = "NONE"


def classify_vqa_error(
    prediction: str,
    reference: str,
    confidence: Optional[float] = None,
    query: Optional[str] = None
) -> ErrorCategory:
    """
    Heuristically categorizes VQA failures into the standardized error taxonomy.
    """
    pred_low = (prediction or "").lower()
    ref_low = (reference or "").lower()
    q_low = (query or "").lower()

    if not pred_low:
        return ErrorCategory.MODEL_FAILURE

    # High confidence on erroneous prediction
    if confidence is not None and confidence >= 0.85:
        return ErrorCategory.OVERCONFIDENT_ERROR

    # Low confidence threshold
    if confidence is not None and confidence < 0.40:
        return ErrorCategory.LOW_CONFIDENCE

    # Temporal query mismatch
    if ("change" in q_low or "t1" in q_low or "t2" in q_low) and ("change" not in pred_low):
        return ErrorCategory.TEMPORAL_REASONING_ERROR

    # Modality / SAR radar query mismatch
    if ("sar" in q_low or "radar" in q_low or "polarization" in q_low) and ("radar" not in pred_low and "backscatter" not in pred_low):
        return ErrorCategory.MODALITY_REASONING_ERROR

    # Counting question
    if any(w in q_low for w in ["how many", "count", "number of"]):
        return ErrorCategory.WRONG_COUNT

    # Location / spatial question
    if any(w in q_low for w in ["where", "location", "north", "south", "east", "west", "corner"]):
        return ErrorCategory.WRONG_LOCATION

    # Default semantic object/attribute mismatch
    if any(c in ref_low for c in ["forest", "water", "urban", "arable", "wetland"]):
        return ErrorCategory.WRONG_OBJECT

    return ErrorCategory.WRONG_ATTRIBUTE
