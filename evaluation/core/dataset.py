"""
Core dataset interface for SatQuery AI Benchmark & Evaluation Engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional
from evaluation.core.sample import BenchmarkSample


class BenchmarkDataset(ABC):
    """
    Abstract Base Class for all benchmark dataset adapters.
    Ensures standard access to samples, metadata, and references across all remote-sensing datasets.
    """

    name: str = "base_dataset"
    version: str = "1.0.0"
    supported_tasks: List[str] = []
    is_available: bool = True
    availability_reason: Optional[str] = None

    @abstractmethod
    def load(self, split: str = "test") -> None:
        """Loads and prepares the dataset split."""
        pass

    @abstractmethod
    def iter_samples(self, limit: Optional[int] = None) -> Iterator[BenchmarkSample]:
        """Iterates over normalized benchmark samples."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns dataset provenance, sensor characteristics, and version metadata."""
        pass

    @abstractmethod
    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        """Extracts task-appropriate ground truth references from sample."""
        pass
