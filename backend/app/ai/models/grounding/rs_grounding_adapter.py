"""
Remote-Sensing Open-Vocabulary Visual Grounding Specialist Model Adapter.
Leverages OWLv2 / OwlViT open-vocabulary detection architecture to locate
referred natural-language spatial objects and terrain features in satellite imagery.
"""

import re
from typing import Any, Dict, List, Optional
from PIL import Image

from app.ai.base import SpecialistModel
from app.ai.exceptions import InferenceError, ModelUnavailableError, UnsupportedModalityError
from app.ai.preprocessing import RemoteSensingPreprocessor
from app.core.logging import logger


class RsGroundingModel(SpecialistModel):
    """
    Open-Vocabulary Grounding Adapter for Remote-Sensing Imagery.
    Extracts spatial regions with per-region confidence scores and normalized bounding boxes.
    """

    name = "remote-sensing-grounding"
    version = "0.1.0"
    task = "grounding"
    supported_modalities = ["optical", "multispectral", "unknown"]

    def __init__(self, model_id: str = "google/owlvit-base-patch32"):
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
            from transformers import OwlViTForObjectDetection, OwlViTProcessor

            logger.info(f"Loading Grounding model '{self.model_id}' onto {device}...")
            self._processor = OwlViTProcessor.from_pretrained(self.model_id)
            self._model = OwlViTForObjectDetection.from_pretrained(self.model_id)
            self._model.to(device)
            self._model.eval()
            self._is_loaded = True
            logger.info(f"Successfully loaded Grounding model '{self.model_id}' on {device}.")
        except ImportError as e:
            logger.error(f"PyTorch or Transformers missing: {e}")
            raise ModelUnavailableError(
                f"Required deep learning libraries not installed: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load Grounding model '{self.model_id}': {e}")
            raise ModelUnavailableError(
                f"Unable to load model '{self.model_id}': {str(e)}"
            ) from e

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided for grounding.")
        modality = metadata.get("modality", "unknown").lower()
        if modality not in self.supported_modalities:
            raise UnsupportedModalityError(
                f"Modality '{modality}' is not supported by {self.name}. "
                f"Supported modalities: {self.supported_modalities}"
            )

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata")
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Locates target regions for referring expression query.
        Returns normalized bounding boxes [x1, y1, x2, y2] in [0..1] range and confidence scores.
        """
        clean_text = self._extract_referring_phrase(query or "target feature")

        if not self._is_loaded or self._model is None or self._processor is None:
            # Fallback if called before loading
            self.load(self._device)

        try:
            import torch

            pil_img = processed_input
            orig_w, orig_h = pil_img.size

            inputs = self._processor(
                text=[[clean_text]],
                images=pil_img,
                return_tensors="pt"
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)

            # Target image sizes (height, width)
            target_sizes = torch.Tensor([[orig_h, orig_w]]).to(self._device)
            results = self._processor.post_process_object_detection(
                outputs=outputs,
                threshold=0.15,
                target_sizes=target_sizes
            )[0]

            boxes = results["boxes"].cpu().numpy()
            scores = results["scores"].cpu().numpy()

            regions = []
            for box, score in zip(boxes, scores):
                x1, y1, x2, y2 = box.tolist()
                # Normalize to 0..1
                norm_x1 = max(0.0, min(1.0, round(x1 / orig_w, 4)))
                norm_y1 = max(0.0, min(1.0, round(y1 / orig_h, 4)))
                norm_x2 = max(norm_x1 + 0.01, min(1.0, round(x2 / orig_w, 4)))
                norm_y2 = max(norm_y1 + 0.01, min(1.0, round(y2 / orig_h, 4)))

                regions.append({
                    "label": clean_text,
                    "confidence": round(float(score), 4),
                    "bbox": [norm_x1, norm_y1, norm_x2, norm_y2]
                })

            # Sort by confidence descending
            regions.sort(key=lambda r: r["confidence"], reverse=True)
            top_regions = regions[:10]  # Cap at top 10 regions

            max_conf = top_regions[0]["confidence"] if top_regions else 0.50
            count = len(top_regions)

            if count > 0:
                answer = f"Detected {count} region(s) corresponding to '{clean_text}'."
            else:
                answer = f"No distinct spatial regions matching '{clean_text}' were located above detection threshold."

            return {
                "task": "grounding",
                "model": {
                    "name": self.name,
                    "version": self.version
                },
                "result": {
                    "answer": answer,
                    "target_expression": clean_text,
                    "region_count": count,
                    "regions": top_regions
                },
                "confidence": {
                    "score": max_conf,
                    "method": "sigmoid_detection_logit"
                },
                "evidence": top_regions
            }

        except Exception as e:
            logger.error(f"Grounding inference failed on '{clean_text}': {e}", exc_info=True)
            raise InferenceError(f"Grounding prediction error: {str(e)}") from e

    @staticmethod
    def _extract_referring_phrase(query: str) -> str:
        """Strips conversational leading words to isolate core target phrase."""
        q = query.lower().strip().rstrip("?.! ")
        patterns = [
            r"^(?:highlight|locate|outline|show me|detect|pinpoint|where is the|where are the|find the)\s+",
            r"^(?:where are|where is)\s+",
        ]
        for pat in patterns:
            q = re.sub(pat, "", q)
        return q.strip() or "region of interest"
