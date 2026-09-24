from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SpecialistModel(ABC):
    """
    Abstract interface for remote-sensing specialist models (Phase 2+).
    Enforces standardized contract across RS-VLM, Object Grounding,
    Change Detection, and Optical-SAR Fusion models.
    """

    name: str
    version: str
    supported_tasks: List[str]  # e.g., ["vqa", "caption", "grounding", "change_detection"]
    supported_modalities: List[str]  # e.g., ["optical", "multispectral", "sar"]

    @abstractmethod
    def validate_input(self, inputs: Dict[str, Any]) -> bool:
        """Validate input raster dimensions, bands, and query parameters."""
        raise NotImplementedError

    @abstractmethod
    def preprocess(self, raw_data: Any) -> Any:
        """Normalize raster bands, apply spectral transformations, or format tensors."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, model_inputs: Any) -> Any:
        """Execute deep learning inference."""
        raise NotImplementedError

    @abstractmethod
    def postprocess(self, raw_outputs: Any) -> Dict[str, Any]:
        """Convert raw logits or feature maps into structured domain outputs."""
        raise NotImplementedError

    @abstractmethod
    def get_evidence(self, raw_outputs: Any) -> Dict[str, Any]:
        """Extract spatial bounding boxes, segmentation masks, or heatmaps."""
        raise NotImplementedError

    @abstractmethod
    def get_confidence(self, raw_outputs: Any) -> float:
        """Calculate calibrated confidence score between 0.0 and 1.0."""
        raise NotImplementedError
