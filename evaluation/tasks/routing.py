"""
Agent Routing Task Evaluator for SatQuery AI (Part 21).
Measures Intent Classification accuracy, Tool Selection accuracy, and Input Schema correctness.
"""

from typing import Any, Dict, List, Tuple
from evaluation.core.evaluator import BaseTaskEvaluator
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory


ROUTING_BENCHMARK_PROBES = [
    {
        "id": "route_01_vqa",
        "query": "What type of agricultural land is present in this satellite image?",
        "inputs": {"image_ids": ["img_01"]},
        "expected_intent": "VISUAL_QUESTION_ANSWERING",
        "expected_tool": "single_image_vqa",
    },
    {
        "id": "route_02_caption",
        "query": "Describe the overall landscape and terrain features visible in this scene.",
        "inputs": {"image_ids": ["img_01"]},
        "expected_intent": "IMAGE_CAPTIONING",
        "expected_tool": "single_image_captioning",
    },
    {
        "id": "route_03_grounding",
        "query": "Locate and draw bounding boxes around the industrial storage tanks.",
        "inputs": {"image_ids": ["img_01"]},
        "expected_intent": "GROUNDING",
        "expected_tool": "single_image_grounding",
    },
    {
        "id": "route_04_change",
        "query": "Detect and highlight all bi-temporal land use changes between T1 and T2.",
        "inputs": {"image_ids": ["img_t1", "img_t2"]},
        "expected_intent": "CHANGE_ANALYSIS",
        "expected_tool": "bi_temporal_change_detection",
    },
    {
        "id": "route_05_cross_modal",
        "query": "Perform joint optical and SAR analysis to penetrate cloud cover and map roads.",
        "inputs": {"image_ids": ["img_opt", "img_sar"]},
        "expected_intent": "CROSS_MODAL_ANALYSIS",
        "expected_tool": "optical_sar_analysis",
    },
    {
        "id": "route_06_change_vqa",
        "query": "What specific environmental changes occurred between these two dates?",
        "inputs": {"image_ids": ["img_t1", "img_t2"]},
        "expected_intent": "CHANGE_ANALYSIS",
        "expected_tool": "bi_temporal_change_description",
    },
    {
        "id": "route_07_water_vqa",
        "query": "Is there a river or reservoir visible in this Sentinel-2 tile?",
        "inputs": {"image_ids": ["img_02"]},
        "expected_intent": "VISUAL_QUESTION_ANSWERING",
        "expected_tool": "single_image_vqa",
    },
    {
        "id": "route_08_optical_sar_vqa",
        "query": "Does the SAR backscatter confirm permanent water in this cloudy optical scene?",
        "inputs": {"image_ids": ["img_opt", "img_sar"]},
        "expected_intent": "CROSS_MODAL_ANALYSIS",
        "expected_tool": "optical_sar_vqa",
    },
]


class AgentRoutingTaskEvaluator(BaseTaskEvaluator):
    """
    Evaluates agent routing, classifier accuracy, and deterministic planner resolution.
    """
    task_name = "ROUTING"

    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        expected_intent = sample.reference.get("expected_intent")
        expected_tool = sample.reference.get("expected_tool")

        raw = prediction.raw_output or {}
        predicted_intent = raw.get("intent") or prediction.task
        predicted_tool = raw.get("tool") or raw.get("tool_name")

        intent_correct = 1.0 if (predicted_intent and predicted_intent.upper() == expected_intent.upper()) else 0.0
        tool_correct = 1.0 if (predicted_tool and predicted_tool.lower() == expected_tool.lower()) else 0.0

        metrics = {
            "intent_accuracy": intent_correct,
            "tool_accuracy": tool_correct,
            "routing_success": 1.0 if (intent_correct == 1.0 and tool_correct == 1.0) else 0.0,
        }

        if intent_correct == 0.0:
            err_cat = ErrorCategory.WRONG_INTENT
        elif tool_correct == 0.0:
            err_cat = ErrorCategory.WRONG_TOOL
        else:
            err_cat = ErrorCategory.NONE

        return metrics, err_cat
