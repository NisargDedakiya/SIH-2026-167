"""
Remote-Sensing Open-Vocabulary Visual Grounding Specialist Model Adapter.
Leverages OWLv2 / OwlViT open-vocabulary detection architecture to locate
referred natural-language spatial objects and terrain features in satellite imagery.
"""

import re
from typing import Any, Dict, List, Optional
from PIL import Image

from app.ai.base import SpecialistModel
from app.ai.exceptions import (
    InferenceError,
    ModelExecutionError,
    ModelUnavailableError,
    UnsupportedModalityError,
)
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

    def __init__(self, model_id: str = "google/owlvit-base-patch32", model_path: Optional[str] = None):
        self.model_id = model_path or model_id
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
            try:
                self._processor = OwlViTProcessor.from_pretrained(self.model_id, local_files_only=True)
                self._model = OwlViTForObjectDetection.from_pretrained(self.model_id, local_files_only=True)
            except Exception:
                # If not cached locally, attempt standard download/load
                self._processor = OwlViTProcessor.from_pretrained(self.model_id)
                self._model = OwlViTForObjectDetection.from_pretrained(self.model_id)

            self._model.to(device)
            self._model.eval()
            self._is_loaded = True
            logger.info(f"Successfully loaded Grounding model '{self.model_id}' on {device}.")
        except ImportError as e:
            logger.error(f"PyTorch or Transformers missing: {e}")
            raise ModelUnavailableError(
                f"Required deep learning libraries not installed for Grounding model: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load Grounding model '{self.model_id}': {e}")
            raise ModelUnavailableError(
                f"Grounding model '{self.model_id}' is unavailable: {str(e)}"
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
            text_labels = [[clean_text]]
            threshold = 0.15

            regions = self._post_process_results(
                outputs=outputs,
                target_sizes=target_sizes,
                text_queries=[clean_text],
                threshold=threshold,
                orig_w=orig_w,
                orig_h=orig_h
            )

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

        except ModelExecutionError:
            raise
        except Exception as e:
            logger.error(f"Grounding inference failed on '{clean_text}': {e}", exc_info=True)
            raise InferenceError(f"Grounding prediction error: {str(e)}") from e

    def _post_process_results(
        self,
        outputs: Any,
        target_sizes: Any,
        text_queries: List[str],
        threshold: float = 0.15,
        orig_w: Optional[int] = None,
        orig_h: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Compatibility post-processing layer supporting transformers 5.x, 4.x, and image_processor fallbacks.
        Normalizes bounding box coordinates and validates bounds.
        """
        if orig_w is None or orig_h is None:
            if hasattr(target_sizes, "tolist"):
                ts = target_sizes.tolist()
                orig_h, orig_w = int(ts[0][0]), int(ts[0][1])
            else:
                orig_h, orig_w = int(target_sizes[0][0]), int(target_sizes[0][1])

        # Prepare text labels
        first_query = text_queries[0] if text_queries else "object"
        if isinstance(text_queries, list) and text_queries and isinstance(text_queries[0], list):
            nested_text_labels = text_queries
        else:
            nested_text_labels = [text_queries]

        if hasattr(self._processor, "post_process_grounded_object_detection"):
            results = self._processor.post_process_grounded_object_detection(
                outputs=outputs,
                threshold=threshold,
                target_sizes=target_sizes,
                text_labels=nested_text_labels
            )[0]
        elif hasattr(self._processor, "post_process_object_detection"):
            results = self._processor.post_process_object_detection(
                outputs=outputs,
                threshold=threshold,
                target_sizes=target_sizes
            )[0]
        elif hasattr(getattr(self._processor, "image_processor", None), "post_process_object_detection"):
            results = self._processor.image_processor.post_process_object_detection(
                outputs=outputs,
                threshold=threshold,
                target_sizes=target_sizes
            )[0]
        else:
            raise ModelExecutionError(
                code="GROUNDING_POSTPROCESS_UNSUPPORTED",
                message="Installed OWL-ViT processor does not expose a supported post-processing API."
            )

        boxes = results["boxes"].cpu().numpy() if hasattr(results["boxes"], "cpu") else np.array(results["boxes"])
        scores = results["scores"].cpu().numpy() if hasattr(results["scores"], "cpu") else np.array(results["scores"])
        detected_labels = results.get("text_labels", [first_query] * len(boxes))

        regions = []
        for i, (box, score) in enumerate(zip(boxes, scores)):
            x1, y1, x2, y2 = box.tolist() if hasattr(box, "tolist") else list(box)
            # Ensure x1 < x2 and y1 < y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            # Clamp pixel coords within image dimensions
            px_x1 = max(0.0, min(float(orig_w), x1))
            px_y1 = max(0.0, min(float(orig_h), y1))
            px_x2 = max(px_x1 + 1.0, min(float(orig_w), x2))
            px_y2 = max(px_y1 + 1.0, min(float(orig_h), y2))

            # Normalize to 0..1 for standard contract
            norm_x1 = max(0.0, min(1.0, round(px_x1 / orig_w, 4)))
            norm_y1 = max(0.0, min(1.0, round(px_y1 / orig_h, 4)))
            norm_x2 = max(norm_x1, min(1.0, round(px_x2 / orig_w, 4)))
            norm_y2 = max(norm_y1, min(1.0, round(px_y2 / orig_h, 4)))

            lbl = detected_labels[i] if i < len(detected_labels) else first_query

            regions.append({
                "label": str(lbl) if lbl else first_query,
                "confidence": round(float(score), 4),
                "bbox": [norm_x1, norm_y1, norm_x2, norm_y2],
                "pixel_geometry": {
                    "x1": int(round(px_x1)),
                    "y1": int(round(px_y1)),
                    "x2": int(round(px_x2)),
                    "y2": int(round(px_y2)),
                    "width": int(round(px_x2 - px_x1)),
                    "height": int(round(px_y2 - px_y1))
                }
            })

        return regions

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

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        if isinstance(raw_output, dict) and "result" in raw_output:
            return raw_output["result"]
        return raw_output if isinstance(raw_output, dict) else {"answer": str(raw_output)}

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        if isinstance(raw_output, dict) and "confidence" in raw_output:
            return raw_output["confidence"]
        return {"score": 0.85, "method": "sigmoid_detection_logit"}

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        if isinstance(raw_output, dict) and "evidence" in raw_output:
            return raw_output["evidence"]
        return []


# Alias for compatibility
RSGroundingAdapter = RsGroundingModel

