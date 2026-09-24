"""
AI Result Postprocessing and Normalization Utilities.
"""

from typing import Any, Dict, List, Optional


class Postprocessor:
    """Utilities for structuring specialist model outputs to match the SatQuery AI Result Contract."""

    @staticmethod
    def format_vqa_result(
        answer: str,
        confidence_score: float,
        confidence_method: str = "token_probability",
        model_name: str = "remote-sensing-vqa",
        model_version: str = "0.1",
        processing_time_ms: int = 0,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return {
            "task": "visual_question_answering",
            "model": {
                "name": model_name,
                "version": model_version,
            },
            "result": {
                "answer": answer.strip(),
            },
            "confidence": {
                "score": round(float(confidence_score), 4),
                "method": confidence_method,
            },
            "evidence": evidence or [],
            "processing_time_ms": processing_time_ms,
        }

    @staticmethod
    def format_caption_result(
        caption: str,
        confidence_score: float,
        confidence_method: str = "beam_log_likelihood",
        model_name: str = "remote-sensing-caption",
        model_version: str = "0.1",
        processing_time_ms: int = 0,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return {
            "task": "image_captioning",
            "model": {
                "name": model_name,
                "version": model_version,
            },
            "result": {
                "caption": caption.strip(),
            },
            "confidence": {
                "score": round(float(confidence_score), 4),
                "method": confidence_method,
            },
            "evidence": evidence or [],
            "processing_time_ms": processing_time_ms,
        }
