"""
Specialist Model Abstract Base Interface for SatQuery AI.

Defines the contract that every remote-sensing AI model adapter must implement.
The API and future Agent routers interact exclusively via this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SpecialistModel(ABC):
    """
    Abstract interface for single-image and multimodal specialist AI models.
    Every model encapsulates its own model-specific weights, preprocessing,
    prediction, confidence calculation, and evidence extraction.
    """

    name: str
    version: str
    task: str
    supported_modalities: List[str]

    @abstractmethod
    def load(self, device: str = "cpu") -> None:
        """
        Load model weights into memory on the target device.
        Must be idempotent and safe to invoke multiple times.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        """
        Validate that the input image and its technical metadata are compatible
        with this specialist model. Raises UnsupportedModalityError or ValueError.
        """
        raise NotImplementedError

    @abstractmethod
    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Any:
        """
        Preprocess the raw image bytes into the format expected by predict()
        (e.g., normalized tensor, PIL Image, or preprocessed raster array).
        """
        raise NotImplementedError

    @abstractmethod
    def predict(self, processed_input: Any, query: Optional[str] = None) -> Any:
        """
        Execute model inference.
        Returns the raw model output structure.
        """
        raise NotImplementedError

    @abstractmethod
    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        """
        Transform raw model outputs into a clean result dictionary.
        For VQA: {'answer': '...'}
        For Caption: {'caption': '...'}
        """
        raise NotImplementedError

    @abstractmethod
    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        """
        Compute or extract confidence score and documentation method.
        Returns: {'score': float, 'method': str}
        """
        raise NotImplementedError

    @abstractmethod
    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        """
        Extract visual or token grounding evidence.
        For Phase 2, this returns an empty list [], reserved for Phase 4 grounding.
        """
        raise NotImplementedError

    def run(
        self,
        image_bytes: bytes,
        metadata: Dict[str, Any],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Standardized end-to-end execution pipeline across all specialist models.
        Returns the normalized AI result contract:
        {
            'task': self.task,
            'model': {'name': self.name, 'version': self.version},
            'result': postprocessed_result,
            'confidence': {'score': float, 'method': str},
            'evidence': [],
            'metadata': {...}
        }
        """
        self.validate_input(image_bytes, metadata)
        processed = self.preprocess(image_bytes, metadata)
        raw_output = self.predict(processed, query=query)
        result = self.postprocess(raw_output)
        conf = self.confidence(raw_output)
        evi = self.evidence(raw_output)

        return {
            "task": self.task,
            "model": {
                "name": self.name,
                "version": self.version,
            },
            "result": result,
            "confidence": conf,
            "evidence": evi,
        }
