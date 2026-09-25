"""
AI ModelRuntime for SatQuery AI.
Manages hardware device detection (auto, cuda, cpu), model lifecycle,
eager/lazy loading, execution timing, and error isolation.
"""

import time
from typing import Any, Dict, Optional
from app.ai.base import SpecialistModel
from app.ai.exceptions import AIError, InferenceError
from app.ai.models.caption.rs_caption_adapter import RsCaptionModel
from app.ai.models.change_detection.rs_change_adapter import RsChangeDetectionModel
from app.ai.models.cross_modal.fusion_model import CrossModalFusionModel
from app.ai.models.grounding.rs_grounding_adapter import RsGroundingModel
from app.ai.models.mock import (
    MockAdaptedVqaModel,
    MockCaptionModel,
    MockChangeDetectionModel,
    MockCrossModalModel,
    MockGroundingModel,
    MockVqaModel,
)
from app.ai.models.vqa.rs_adapted_vqa import RsAdaptedVqaModel
from app.ai.models.vqa.rs_vqa_adapter import RsVqaModel
from app.ai.registry import ModelRegistry, get_model_registry
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class ModelRuntime:
    """
    Manages execution lifecycle, memory residency, and device placement for specialist AI models.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()
        self.device = self._resolve_device(settings.AI_DEVICE)
        self._loaded_models = set()
        logger.info(f"ModelRuntime initialized using device: {self.device}")

    @staticmethod
    def _resolve_device(config_device: str) -> str:
        """
        Determines execution target: auto, cuda, or cpu.
        Never crashes on CPU-only machines.
        """
        target = (config_device or "auto").lower().strip()
        if target == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                logger.warning("CUDA requested but not available. Falling back to CPU.")
            except ImportError:
                logger.warning("PyTorch not installed. Falling back to CPU.")
            return "cpu"
        elif target == "cpu":
            return "cpu"
        else:  # 'auto'
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass
            return "cpu"

    def initialize_models(self) -> None:
        """
        Registers default specialist models into the registry based on settings.
        If AI_USE_MOCK is True, registers fast mock models for unit tests.
        Otherwise registers real RS VQA, RS Caption, and RS-Adapted models.
        """
        if settings.AI_USE_MOCK:
            logger.info("Initializing ModelRuntime in MOCK mode (fast deterministic testing).")
            # Phase 7: Register RS-Adapted model satquery-rs-v1 as default VQA model
            adapted_vqa_mock = MockAdaptedVqaModel()
            vqa_mock = MockVqaModel()
            caption_mock = MockCaptionModel()
            grounding_mock = MockGroundingModel()
            change_mock = MockChangeDetectionModel()
            cross_modal_mock = MockCrossModalModel()

            self.registry.register(adapted_vqa_mock, default_for_task=True)
            self.registry.register(vqa_mock, default_for_task=False, aliases=["remote-sensing-vqa"])
            self.registry.register(caption_mock, default_for_task=True, aliases=["remote-sensing-caption"])
            self.registry.register(grounding_mock, default_for_task=True, aliases=["remote-sensing-grounding"])
            self.registry.register(change_mock, default_for_task=True, aliases=["remote-sensing-change", "remote-sensing-siam-diff"])
            self.registry.register(cross_modal_mock, default_for_task=True, aliases=["remote-sensing-cross-modal", "optical-sar-fusion-baseline"])
        else:
            logger.info("Initializing ModelRuntime with Remote-Sensing Specialist Models.")
            # Phase 7: Domain-adapted model satquery-rs-v1 is default for remote-sensing VQA
            adapted_vqa = RsAdaptedVqaModel(base_model_id=settings.AI_VQA_MODEL)
            vqa_model = RsVqaModel(model_id=settings.AI_VQA_MODEL)
            caption_model = RsCaptionModel(model_id=settings.AI_CAPTION_MODEL)
            grounding_model = RsGroundingModel(model_id=settings.AI_GROUNDING_MODEL)
            change_model = RsChangeDetectionModel()
            cross_modal_model = CrossModalFusionModel()

            self.registry.register(adapted_vqa, default_for_task=True)
            self.registry.register(vqa_model, default_for_task=False)
            self.registry.register(caption_model, default_for_task=True)
            self.registry.register(grounding_model, default_for_task=True)
            self.registry.register(change_model, default_for_task=True, aliases=["remote-sensing-siam-diff"])
            self.registry.register(cross_modal_model, default_for_task=True, aliases=["optical-sar-fusion-baseline"])

            # Also register mock models under distinct names so tests can explicitly target them
            self.registry.register(MockAdaptedVqaModel(), default_for_task=False)
            self.registry.register(MockVqaModel(), default_for_task=False)
            self.registry.register(MockCaptionModel(), default_for_task=False)
            self.registry.register(MockGroundingModel(), default_for_task=False)
            self.registry.register(MockChangeDetectionModel(), default_for_task=False)
            self.registry.register(MockCrossModalModel(), default_for_task=False)

    def get_model_for_task(self, task: str) -> Optional[SpecialistModel]:
        """Retrieves default model for a given task, returning None if not found."""
        try:
            return self.registry.get_by_task(task)
        except Exception:
            return None

    def load_model(self, model: SpecialistModel) -> None:
        """Loads a model onto the configured device once and caches it in memory."""
        if model.name not in self._loaded_models:
            logger.info(f"Ensuring model '{model.name}' is loaded on {self.device}...")
            model.load(self.device)
            self._loaded_models.add(model.name)

    def execute(
        self,
        model: SpecialistModel,
        image_bytes: bytes,
        metadata: Dict[str, Any],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a specialist model with timing instrumentation and unified error capture.
        Returns the normalized AI result contract.
        If an RS-adapted model is requested but checkpoint is unavailable, performs documented fallback.
        """
        start_time = time.time()
        active_model = model
        fallback_record: Optional[Dict[str, str]] = None

        try:
            self.load_model(active_model)
        except Exception as load_err:
            if getattr(active_model, "is_adapted", False) or active_model.name == "satquery-rs-v1":
                logger.warning(
                    f"Model: Fallback Reason: RS-adapted checkpoint unavailable ({load_err}). "
                    f"Falling back to baseline VQA model."
                )
                fallback_record = {
                    "fallback_model": "remote-sensing-vqa-baseline",
                    "reason": f"RS-adapted checkpoint unavailable: {str(load_err)}"
                }
                # Retrieve baseline model
                baseline_name = "remote-sensing-vqa-mock" if settings.AI_USE_MOCK else "remote-sensing-vqa"
                if baseline_name in self.registry._models:
                    active_model = self.registry.get(baseline_name)
                elif "remote-sensing-vqa-mock" in self.registry._models:
                    active_model = self.registry.get("remote-sensing-vqa-mock")
                elif "remote-sensing-vqa" in self.registry._models:
                    active_model = self.registry.get("remote-sensing-vqa")
                else:
                    alt_candidates = [
                        m for m in self.registry._models.values()
                        if m.task == active_model.task and m.name != active_model.name
                    ]
                    if alt_candidates:
                        active_model = alt_candidates[0]
                    else:
                        raise
                self.load_model(active_model)
            else:
                raise

        try:
            result_contract = active_model.run(
                image_bytes=image_bytes,
                metadata=metadata,
                query=query
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result_contract["processing_time_ms"] = duration_ms

            if fallback_record:
                result_contract["fallback"] = fallback_record

            logger.info(
                f"Model '{active_model.name}' completed task '{active_model.task}' in {duration_ms}ms.",
                extra={
                    "model": active_model.name,
                    "task": active_model.task,
                    "duration_ms": duration_ms,
                    "confidence": result_contract.get("confidence", {}).get("score")
                }
            )
            return result_contract

        except AIError:
            raise
        except Exception as e:
            logger.error(f"Inference execution failed on model '{model.name}': {e}")
            raise InferenceError(f"Model '{model.name}' execution failed: {str(e)}") from e


# Global runtime singleton
runtime: Optional[ModelRuntime] = None


def get_model_runtime() -> ModelRuntime:
    global runtime
    if runtime is None or len(runtime.registry.list_models()) == 0:
        rt = ModelRuntime()
        rt.initialize_models()
        runtime = rt
    return runtime


get_runtime = get_model_runtime

