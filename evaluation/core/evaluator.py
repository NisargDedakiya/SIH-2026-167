"""
Base Task Evaluator interface for SatQuery AI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
from evaluation.core.sample import BenchmarkSample
from evaluation.core.prediction import ModelPrediction
from evaluation.core.errors import ErrorCategory


class BaseTaskEvaluator(ABC):
    """
    Abstract evaluator for a specific remote-sensing task.
    """
    task_name: str = "base_task"

    @abstractmethod
    def evaluate_sample(
        self,
        sample: BenchmarkSample,
        prediction: ModelPrediction
    ) -> Tuple[Dict[str, float], ErrorCategory]:
        """
        Evaluates a single prediction against the sample ground truth reference.
        Returns:
            metrics: Dict mapping metric names to scalar values.
            error_category: Categorized ErrorCategory if failed, else ErrorCategory.NONE.
        """
        pass
