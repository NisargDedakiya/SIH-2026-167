"""
SatQuery AI — Benchmark & Evaluation Engine (Phase 8).
"""

from evaluation.core.registry import (
    get_benchmark_registry,
    get_task_registry,
    benchmark_registry,
    task_registry,
)
from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.runner import EvaluationRunner

# Dataset Adapters
from evaluation.datasets.bigearthnet.adapter import BigEarthNetBenchmarkAdapter
from evaluation.datasets.vrsbench.adapter import VRSBenchAdapter
from evaluation.datasets.rsvqa.adapter import RSVQAAdapter
from evaluation.datasets.cdvqa.adapter import CDVQAAdapter
from evaluation.datasets.isro_sac.adapter import ISROSACAdapter

# Task Evaluators
from evaluation.tasks.vqa import VQATaskEvaluator
from evaluation.tasks.captioning import CaptioningTaskEvaluator
from evaluation.tasks.grounding import GroundingTaskEvaluator
from evaluation.tasks.change_detection import ChangeDetectionTaskEvaluator
from evaluation.tasks.change_vqa import ChangeVQATaskEvaluator
from evaluation.tasks.cross_modal import CrossModalTaskEvaluator
from evaluation.tasks.routing import AgentRoutingTaskEvaluator


def initialize_evaluation_registries() -> None:
    """Populates global benchmark and task registries with standard adapters."""
    # Datasets
    benchmark_registry.register(BigEarthNetBenchmarkAdapter())
    benchmark_registry.register(VRSBenchAdapter())
    benchmark_registry.register(RSVQAAdapter())
    benchmark_registry.register(CDVQAAdapter())
    benchmark_registry.register(ISROSACAdapter())

    # Tasks
    task_registry.register(VQATaskEvaluator())
    task_registry.register(CaptioningTaskEvaluator())
    task_registry.register(GroundingTaskEvaluator())
    task_registry.register(ChangeDetectionTaskEvaluator())
    task_registry.register(ChangeVQATaskEvaluator())
    task_registry.register(CrossModalTaskEvaluator())
    task_registry.register(AgentRoutingTaskEvaluator())


# Auto-initialize on import
initialize_evaluation_registries()

__all__ = [
    "get_benchmark_registry",
    "get_task_registry",
    "benchmark_registry",
    "task_registry",
    "BenchmarkDataset",
    "BenchmarkSample",
    "ModelPrediction",
    "EvaluationRunner",
    "BigEarthNetBenchmarkAdapter",
    "VRSBenchAdapter",
    "RSVQAAdapter",
    "CDVQAAdapter",
    "ISROSACAdapter",
    "initialize_evaluation_registries",
]
