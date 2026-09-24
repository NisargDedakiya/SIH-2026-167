"""
Registries for benchmark datasets and evaluation tasks.
"""

from typing import Any, Dict, List, Optional, Type
from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.evaluator import BaseTaskEvaluator


class BenchmarkRegistry:
    """Central registry of all benchmark dataset adapters."""

    def __init__(self):
        self._datasets: Dict[str, BenchmarkDataset] = {}

    def register(self, dataset: BenchmarkDataset) -> None:
        self._datasets[dataset.name.lower()] = dataset

    def get(self, name: str) -> Optional[BenchmarkDataset]:
        return self._datasets.get(name.lower())

    def list(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": d.name,
                "version": d.version,
                "supported_tasks": d.supported_tasks,
                "is_available": d.is_available,
                "availability_reason": d.availability_reason,
            }
            for d in self._datasets.values()
        ]

    def find_by_task(self, task: str) -> List[BenchmarkDataset]:
        task_low = task.lower()
        return [d for d in self._datasets.values() if task_low in [t.lower() for t in d.supported_tasks]]


class EvaluationTaskRegistry:
    """Central registry of all evaluation task evaluators."""

    def __init__(self):
        self._tasks: Dict[str, BaseTaskEvaluator] = {}

    def register(self, evaluator: BaseTaskEvaluator) -> None:
        self._tasks[evaluator.task_name.lower()] = evaluator

    def get(self, task_name: str) -> Optional[BaseTaskEvaluator]:
        return self._tasks.get(task_name.lower())

    def list_tasks(self) -> List[str]:
        return list(self._tasks.keys())


# Singleton instances
benchmark_registry = BenchmarkRegistry()
task_registry = EvaluationTaskRegistry()


def get_benchmark_registry() -> BenchmarkRegistry:
    return benchmark_registry


def get_task_registry() -> EvaluationTaskRegistry:
    return task_registry
