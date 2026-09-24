"""
Real Remote-Sensing VQA Model Adapter.
Wraps Vision-Language models (e.g., Salesforce/blip-vqa-base) with
remote-sensing prompt grounding, raster preprocessing, and token-probability confidence.
"""

from typing import Any, Dict, List, Optional
from PIL import Image

from app.ai.base import SpecialistModel
from app.ai.exceptions import InferenceError, ModelUnavailableError, UnsupportedModalityError
from app.ai.preprocessing import RemoteSensingPreprocessor
from app.core.logging import logger


class RsVqaModel(SpecialistModel):
    """
    Remote-Sensing Visual Question Answering Specialist Model.
    Supports optical and multispectral imagery normalized through RemoteSensingPreprocessor.
    """
    name = "remote-sensing-vqa"
    version = "0.1.0"
    task = "visual_question_answering"
    supported_modalities = ["optical", "multispectral", "unknown"]

    def __init__(self, model_id: str = "Salesforce/blip-vqa-base"):
        self.model_id = model_id
        self._processor = None
        self._model = None
        self._device = "cpu"
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        if self._is_loaded and self._device == device:
            return

        self._device = device
        try:
            import torch
            from transformers import BlipForQuestionAnswering, BlipProcessor

            logger.info(f"Loading Remote-Sensing VQA model '{self.model_id}' onto {device}...")
            self._processor = BlipProcessor.from_pretrained(self.model_id)
            self._model = BlipForQuestionAnswering.from_pretrained(self.model_id)
            self._model.to(device)
            self._model.eval()
            self._is_loaded = True
            logger.info(f"Successfully loaded VQA model '{self.model_id}' on {device}.")
        except ImportError as e:
            logger.error(f"PyTorch or Transformers missing: {e}")
            raise ModelUnavailableError(
                f"Required deep learning libraries not installed: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load VQA model '{self.model_id}': {e}")
            raise ModelUnavailableError(
                f"Unable to load model '{self.model_id}': {str(e)}"
            ) from e

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Input image cannot be empty.")
        modality = metadata.get("modality", "unknown").lower()
        if modality not in self.supported_modalities:
            raise UnsupportedModalityError(
                f"Modality '{modality}' is not supported by {self.name}. "
                f"Supported: {self.supported_modalities}"
            )

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata"),
            target_size=(384, 384)
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        if not self._is_loaded:
            self.load(self._device)

        if not query or not query.strip():
            raise ValueError("Query string cannot be empty for Visual Question Answering.")

        try:
            import torch

            # Remote-sensing prompt grounding: prompt context for satellite imagery
            rs_context_prompt = f"Satellite image query: {query.strip()}"

            inputs = self._processor(
                images=processed_input,
                text=rs_context_prompt,
                return_tensors="pt"
            ).to(self._device)

            with torch.no_grad():
                generated_outputs = self._model.generate(
                    **inputs,
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_new_tokens=48
                )

            # Decode text
            answer_ids = generated_outputs.sequences[0]
            answer_text = self._processor.decode(answer_ids, skip_special_tokens=True)

            # Calibrate confidence using output logits probabilities
            confidence_score = 0.85
            if generated_outputs.scores:
                step_probs = []
                for step_logits in generated_outputs.scores:
                    prob = torch.softmax(step_logits[0], dim=-1)
                    max_prob = torch.max(prob).item()
                    step_probs.append(max_prob)
                if step_probs:
                    confidence_score = sum(step_probs) / len(step_probs)

            return {
                "answer": answer_text,
                "confidence_score": confidence_score,
                "confidence_method": "token_probability"
            }

        except Exception as e:
            logger.error(f"VQA prediction failed: {e}")
            raise InferenceError(f"VQA model inference failed: {str(e)}") from e

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {"answer": raw_output["answer"]}

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": round(float(raw_output.get("confidence_score", 0.85)), 4),
            "method": raw_output.get("confidence_method", "token_probability"),
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        # Reserved for Phase 4 Grounding
        return []
