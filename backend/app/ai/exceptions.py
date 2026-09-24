"""
Exceptions for SatQuery Remote-Sensing AI runtime and specialist models.
"""

class AIError(Exception):
    """Base exception for all AI runtime errors."""
    pass


class ModelNotFoundError(AIError):
    """Raised when a requested model or task cannot be found in the registry."""
    pass


class UnsupportedModalityError(AIError):
    """Raised when an image's modality or format is not supported by the specialist model."""
    pass


class PreprocessingError(AIError):
    """Raised when raster band extraction, scaling, or tensor formatting fails."""
    pass


class InferenceError(AIError):
    """Raised when model forward pass or generation fails."""
    pass


class ModelUnavailableError(AIError):
    """Raised when the requested model cannot be initialized or loaded."""
    pass


class AdapterArchitectureMismatchError(AIError):
    """Raised when an adapter checkpoint does not match the base model architecture or target modules."""
    def __init__(self, message: str, missing_keys: list = None, unexpected_keys: list = None):
        super().__init__(message)
        self.code = "ADAPTER_ARCHITECTURE_MISMATCH"
        self.missing_keys = missing_keys or []
        self.unexpected_keys = unexpected_keys or []

