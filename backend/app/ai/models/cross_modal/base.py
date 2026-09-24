"""
Abstract Base Interface for Cross-Modal Optical-SAR Specialist Models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np


class CrossModalModel(ABC):
    """
    Abstract interface for specialist models operating on co-registered Optical and SAR images.
    Stage A (Optical/SAR Encoders) -> Stage B (Cross-Modal Fusion) -> Stage C (Task Reasoning).
    """

    name: str
    version: str
    task: str = "cross_modal_analysis"
    supported_modalities: List[str] = ["optical", "multispectral", "sar"]

    @abstractmethod
    def load(self, device: str = "cpu") -> None:
        """Loads weights onto target device."""
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        processed_input: Dict[str, np.ndarray],
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes cross-modal prediction.
        processed_input: {"optical": ndarray[H, W, C_opt], "sar": ndarray[H, W, C_sar]}
        query: User natural language instruction or question.
        Returns:
            {
                "answer": str,
                "confidence_score": float,
                "confidence_method": str,
                "optical_signal": Dict[str, Any],
                "sar_signal": Dict[str, Any],
                "regions": List[Dict[str, Any]],
                "task": str,
            }
        """
        raise NotImplementedError

    @abstractmethod
    def unload(self) -> None:
        """Releases GPU/CPU resources."""
        raise NotImplementedError
