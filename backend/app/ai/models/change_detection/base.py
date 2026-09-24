"""
Abstract Base Interface for Bi-Temporal Change Detection Specialist Models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np


class ChangeDetectionModel(ABC):
    """
    Abstract interface for specialist models operating on bi-temporal image pairs (T1 and T2).
    """

    name: str
    version: str
    task: str = "change_analysis"
    supported_modalities: List[str]

    @abstractmethod
    def load(self, device: str = "cpu") -> None:
        """Loads weights onto the target device."""
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        processed_input: Dict[str, np.ndarray],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes change detection inference.
        processed_input: {"t1": ndarray[H, W, 3], "t2": ndarray[H, W, 3]}
        Returns:
            {
                "change_mask": ndarray[H, W] (uint8 0 or 1),
                "change_scores": ndarray[H, W] (float32 [0..1]),
                "change_score": float,
                "confidence_score": float,
                "confidence_method": str,
                "task": "change_analysis"
            }
        """
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Releases GPU/CPU memory."""
        raise NotImplementedError
