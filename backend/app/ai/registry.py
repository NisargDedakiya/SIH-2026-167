"""
Model Registry for SatQuery AI.
Maintains available specialist models, task mappings, and metadata.
Decouples API routes and future Agent routers from concrete model implementations.
"""

from typing import Any, Dict, List, Optional
from app.ai.base import SpecialistModel
from app.ai.exceptions import ModelNotFoundError
from app.core.logging import logger


class ModelRegistry:
    """
    Central registry for specialist AI models.
    Supports registration, task resolution, and model metadata enumeration.
    """

    def __init__(self):
        self._models: Dict[str, SpecialistModel] = {}
        self._task_map: Dict[str, str] = {}

    def register(
        self,
        model: SpecialistModel,
        default_for_task: bool = True,
        aliases: Optional[List[str]] = None
    ) -> None:
        """
        Register a specialist model instance.
        """
        self._models[model.name] = model
        if aliases:
            for alias in aliases:
                self._models[alias] = model
        if default_for_task or model.task not in self._task_map:
            self._task_map[model.task] = model.name
        logger.info(
            f"Registered model '{model.name}' (v{model.version}) for task '{model.task}'."
        )

    def get(self, name: str) -> SpecialistModel:
        """
        Retrieve a registered specialist model by name.
        """
        if name not in self._models:
            raise ModelNotFoundError(
                f"Model '{name}' is not registered. Available: {list(self._models.keys())}"
            )
        return self._models[name]

    def get_by_task(self, task: str) -> SpecialistModel:
        """
        Retrieve the default specialist model for a specific task.
        """
        task_aliases = {
            "vqa": "visual_question_answering",
            "caption": "image_captioning",
            "grounding": "grounding",
            "change": "change_analysis",
            "cross_modal": "cross_modal_analysis",
        }
        canonical_task = task_aliases.get(task, task)
        if canonical_task not in self._task_map:
            raise ModelNotFoundError(
                f"No specialist model registered for task '{task}' (resolved: '{canonical_task}'). "
                f"Available tasks: {list(self._task_map.keys())}"
            )
        model_name = self._task_map[canonical_task]
        return self._models[model_name]

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Enumerate all registered models and their capability metadata.
        """
        result = []
        seen = set()
        for name, model in self._models.items():
            if model.name in seen:
                continue
            seen.add(model.name)
            result.append({
                "name": model.name,
                "version": model.version,
                "task": model.task,
                "supported_modalities": model.supported_modalities,
                "is_default_for_task": (self._task_map.get(model.task) == model.name),
                "is_adapted": getattr(model, "is_adapted", False),
                "adapter_type": getattr(model, "adapter_type", None),
                "dataset_provenance": getattr(model, "dataset_provenance", None),
                "base_model": getattr(model, "base_model_id", getattr(model, "model_id", None)),
            })
        return result

    def clear(self) -> None:
        """Clear all registered models (useful in test teardown)."""
        self._models.clear()
        self._task_map.clear()


# Global singleton registry instance
registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return registry
