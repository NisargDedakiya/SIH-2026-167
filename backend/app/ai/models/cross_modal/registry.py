"""
Cross-Modal Model Registry and Factory.
"""

from typing import Dict, List, Optional
from app.ai.models.cross_modal.base import CrossModalModel
from app.ai.models.cross_modal.fusion_model import CrossModalFusionModel


class CrossModalModelRegistry:
    """Registry maintaining active and experimental Optical-SAR specialist models."""

    def __init__(self):
        self._models: Dict[str, CrossModalModel] = {}
        # Register default baseline model
        self.register(CrossModalFusionModel())

    def register(self, model: CrossModalModel) -> None:
        self._models[model.name] = model

    def get(self, name: str) -> Optional[CrossModalModel]:
        return self._models.get(name)

    def list_models(self) -> List[CrossModalModel]:
        return list(self._models.values())


_cross_modal_registry: Optional[CrossModalModelRegistry] = None


def get_cross_modal_model_registry() -> CrossModalModelRegistry:
    global _cross_modal_registry
    if _cross_modal_registry is None:
        _cross_modal_registry = CrossModalModelRegistry()
    return _cross_modal_registry
