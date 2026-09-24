"""
Deterministic Mock Specialist Models for Fast CI/Unit Testing & Development.
Ensures raster decoding, validation, and API contracts are 100% verified
without requiring multi-gigabyte HuggingFace weight downloads during testing.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image

from app.ai.base import SpecialistModel
from app.ai.exceptions import UnsupportedModalityError
from app.ai.preprocessing import RemoteSensingPreprocessor


class MockVqaModel(SpecialistModel):
    """
    Mock Remote-Sensing VQA Model implementing the full SpecialistModel interface.
    """
    name = "remote-sensing-vqa-mock"
    version = "0.1.0"
    task = "visual_question_answering"
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]

    def __init__(self):
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")
        modality = metadata.get("modality", "unknown").lower()
        if modality not in self.supported_modalities:
            raise UnsupportedModalityError(
                f"Modality '{modality}' is not supported by {self.name}."
            )

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        # Exercises real raster decoding and normalization
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata")
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        q = (query or "").lower().strip()

        if "land cover" in q:
            ans = "The scene primarily contains agricultural land with patches of dense vegetation and scattered built-up structures."
            conf = 0.89
        elif "water" in q or "river" in q or "lake" in q:
            ans = "A distinct natural water body is visible traversing the central region of the scene."
            conf = 0.92
        elif "building" in q or "urban" in q or "structure" in q:
            ans = "Dense commercial and residential structures are visible with interconnected road networks."
            conf = 0.86
        elif "forest" in q or "tree" in q or "vegetation" in q:
            ans = "Extensive canopy cover and green vegetation occupy a significant portion of the image."
            conf = 0.91
        else:
            ans = "Remote-sensing analysis indicates an active terrestrial landscape featuring mixed vegetation and infrastructure."
            conf = 0.85

        return {
            "answer": ans,
            "confidence_score": conf,
            "confidence_method": "simulated_model_probability"
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {"answer": raw_output["answer"]}

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output["confidence_score"],
            "method": raw_output["confidence_method"],
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return []


class MockCaptionModel(SpecialistModel):
    """
    Mock Remote-Sensing Captioning Model implementing the full SpecialistModel interface.
    """
    name = "remote-sensing-caption-mock"
    version = "0.1.0"
    task = "image_captioning"
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]

    def __init__(self):
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")
        modality = metadata.get("modality", "unknown").lower()
        if modality not in self.supported_modalities:
            raise UnsupportedModalityError(
                f"Modality '{modality}' is not supported by {self.name}."
            )

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata")
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        caption = "A high-resolution remote-sensing scene showing a predominantly agricultural and semi-urban landscape with roads, green canopy, and buildings."
        return {
            "caption": caption,
            "confidence_score": 0.88,
            "confidence_method": "simulated_beam_log_likelihood"
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {"caption": raw_output["caption"]}

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output["confidence_score"],
            "method": raw_output["confidence_method"],
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return []


class MockGroundingModel(SpecialistModel):
    """
    Mock Remote-Sensing Grounding Model implementing the full SpecialistModel interface.
    Generates deterministic spatial bounding boxes and visual evidence for CI and unit tests.
    """
    name = "remote-sensing-grounding-mock"
    version = "0.1.0"
    task = "grounding"
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]

    def __init__(self):
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")
        modality = metadata.get("modality", "unknown").lower()
        if modality not in self.supported_modalities:
            raise UnsupportedModalityError(
                f"Modality '{modality}' is not supported by {self.name}."
            )

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata")
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        q = (query or "").lower().strip()

        if "water" in q or "river" in q or "lake" in q:
            label = "water body"
            regions = [
                {
                    "label": "water body",
                    "confidence": 0.91,
                    "bbox": [0.25, 0.50, 0.75, 0.85]
                }
            ]
            answer = "The image contains a prominent water body situated in the southern portion of the scene."
        elif "building" in q or "structure" in q or "urban" in q:
            label = "building cluster"
            regions = [
                {
                    "label": "commercial structure",
                    "confidence": 0.89,
                    "bbox": [0.12, 0.15, 0.42, 0.45]
                },
                {
                    "label": "residential building",
                    "confidence": 0.83,
                    "bbox": [0.55, 0.20, 0.85, 0.52]
                }
            ]
            answer = "Identified 2 primary building clusters with interconnected access roadways."
        elif "road" in q:
            label = "road network"
            regions = [
                {
                    "label": "arterial road",
                    "confidence": 0.87,
                    "bbox": [0.05, 0.45, 0.95, 0.58]
                }
            ]
            answer = "Detected an arterial road network traversing horizontally across the scene."
        elif "agriculture" in q or "vegetation" in q or "forest" in q:
            label = "agricultural vegetation"
            regions = [
                {
                    "label": "agricultural parcel",
                    "confidence": 0.90,
                    "bbox": [0.10, 0.10, 0.65, 0.70]
                }
            ]
            answer = "Located expansive agricultural vegetation plots spanning the north-western sector."
        else:
            label = "region of interest"
            regions = [
                {
                    "label": "region of interest",
                    "confidence": 0.85,
                    "bbox": [0.20, 0.20, 0.80, 0.80]
                }
            ]
            answer = "Located target spatial feature matching the query."

        return {
            "task": "grounding",
            "answer": answer,
            "target_expression": label,
            "region_count": len(regions),
            "regions": regions,
            "confidence_score": max(r["confidence"] for r in regions),
            "confidence_method": "deterministic_spatial_prior"
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "answer": raw_output["answer"],
            "regions": raw_output["regions"],
            "region_count": raw_output["region_count"]
        }

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output["confidence_score"],
            "method": raw_output["confidence_method"],
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return raw_output.get("regions", [])


class MockChangeDetectionModel(SpecialistModel):
    """
    Mock Remote-Sensing Change Detection Model for testing and offline CI/CD.
    Generates deterministic, spatially bounded change masks and statistical metrics.
    """
    name = "remote-sensing-change-mock"
    version = "0.1.0"
    task = "change_analysis"
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]

    def __init__(self):
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def unload(self) -> None:
        self._is_loaded = False

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Any:
        return image_bytes

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        if isinstance(processed_input, dict) and "t1" in processed_input:
            t1 = processed_input["t1"]
            h, w = t1.shape[:2]
        elif hasattr(processed_input, "shape"):
            h, w = processed_input.shape[:2]
        else:
            h, w = 128, 128

        q = (query or "").lower().strip()
        change_mask = np.zeros((h, w), dtype=np.uint8)
        change_scores = np.zeros((h, w), dtype=np.float32)

        if "water" in q or "river" in q or "lake" in q:
            # Bottom quadrant change (water body shift)
            y1, y2 = int(h * 0.55), int(h * 0.85)
            x1, x2 = int(w * 0.25), int(w * 0.75)
            change_mask[y1:y2, x1:x2] = 1
            change_scores[y1:y2, x1:x2] = 0.91
        elif "building" in q or "construction" in q or "urban" in q:
            # 2 distinct building expansion clusters
            # Cluster 1 (north-west)
            y1, y2 = int(h * 0.15), int(h * 0.35)
            x1, x2 = int(w * 0.15), int(w * 0.40)
            change_mask[y1:y2, x1:x2] = 1
            change_scores[y1:y2, x1:x2] = 0.92

            # Cluster 2 (north-east)
            y3, y4 = int(h * 0.20), int(h * 0.42)
            x3, x4 = int(w * 0.60), int(w * 0.85)
            change_mask[y3:y4, x3:x4] = 1
            change_scores[y3:y4, x3:x4] = 0.88
        elif "road" in q:
            # Linear corridor change
            y1, y2 = int(h * 0.48), int(h * 0.52)
            change_mask[y1:y2, :] = 1
            change_scores[y1:y2, :] = 0.87
        else:
            # General multi-region change
            y1, y2 = int(h * 0.20), int(h * 0.40)
            x1, x2 = int(w * 0.20), int(w * 0.45)
            change_mask[y1:y2, x1:x2] = 1
            change_scores[y1:y2, x1:x2] = 0.90

            y3, y4 = int(h * 0.60), int(h * 0.78)
            x3, x4 = int(w * 0.55), int(w * 0.80)
            change_mask[y3:y4, x3:x4] = 1
            change_scores[y3:y4, x3:x4] = 0.86

        total_px = h * w
        changed_px = int(np.sum(change_mask))
        change_pct = round((changed_px / total_px) * 100.0, 2)

        return {
            "task": "change_analysis",
            "change_mask": change_mask,
            "change_scores": change_scores,
            "change_score": round(change_pct / 100.0, 4),
            "change_percentage": change_pct,
            "confidence_score": 0.89,
            "confidence_method": "deterministic_bitemporal_prior",
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "change_score": raw_output.get("change_score", 0.0),
            "change_percentage": raw_output.get("change_percentage", 0.0),
            "changed": raw_output.get("change_score", 0.0) > 0.0,
        }

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output.get("confidence_score", 0.89),
            "method": raw_output.get("confidence_method", "deterministic_bitemporal_prior"),
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return []


class MockCrossModalModel(SpecialistModel):
    """
    Deterministic Mock Cross-Modal Optical-SAR Specialist Model for CI & Unit Testing.
    Clearly marked with mock=True.
    """
    name = "remote-sensing-cross-modal-mock"
    version = "0.1.0"
    task = "cross_modal_analysis"
    supported_modalities = ["optical", "multispectral", "sar"]
    mock: bool = True

    def __init__(self):
        self._is_loaded = False

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def unload(self) -> None:
        self._is_loaded = False

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Any:
        return image_bytes

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        q = (query or "").lower().strip()

        regions = []
        if "water" in q or "river" in q or "lake" in q:
            answer = "Water body localized via optical NIR absorption and SAR radar specular reflection null."
            regions.append({
                "label": "water body",
                "confidence": 0.94,
                "bbox": [0.35, 0.20, 0.70, 0.80],
                "supported_by": "both",
                "rationale": "High absorption in optical and dark specular return in SAR."
            })
            conf = 0.94
        elif "urban" in q or "building" in q or "structure" in q or "infrastructure" in q:
            answer = "Urban built-up area confirmed by optical geometric rooftops and SAR double-bounce corner reflection."
            regions.append({
                "label": "urban core",
                "confidence": 0.92,
                "bbox": [0.15, 0.15, 0.55, 0.60],
                "supported_by": "both",
                "rationale": "Rooftop geometry with cardinal double bounce."
            })
            conf = 0.92
        elif "agriculture" in q or "crop" in q or "vegetation" in q:
            answer = "Agricultural plots confirmed via optical green vegetation index and radar canopy depolarizing volume scattering."
            regions.append({
                "label": "agricultural parcel",
                "confidence": 0.90,
                "bbox": [0.10, 0.50, 0.45, 0.90],
                "supported_by": "both",
                "rationale": "Chlorophyll optical reflectance matching radar canopy volume scattering."
            })
            conf = 0.90
        elif "reveal" in q or "does not" in q or "difficult to see" in q:
            answer = "SAR reveals cardinal dielectric surface roughness and structural corner reflections independent of visual lighting."
            regions.append({
                "label": "structural feature prominent in SAR",
                "confidence": 0.91,
                "bbox": [0.25, 0.25, 0.70, 0.75],
                "supported_by": "sar",
                "rationale": "Dielectric surface roughness resolved clearly through microwave penetration."
            })
            conf = 0.91
        else:
            answer = "Joint optical-SAR cross-modal analysis resolved complementary spectral and microwave structural evidence."
            regions.append({
                "label": "fused region of interest",
                "confidence": 0.89,
                "bbox": [0.20, 0.20, 0.80, 0.80],
                "supported_by": "both",
                "rationale": "Co-registered multi-modal feature cluster."
            })
            conf = 0.89

        return {
            "task": "cross_modal_analysis",
            "answer": answer,
            "confidence_score": conf,
            "confidence_method": "deterministic_cross_modal_prior",
            "optical_signal": {"detected": True, "confidence": conf},
            "sar_signal": {"detected": True, "confidence": conf},
            "regions": regions,
            "mock": True,
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {"answer": raw_output.get("answer", "")}

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output.get("confidence_score", 0.90),
            "method": raw_output.get("confidence_method", "deterministic_cross_modal_prior"),
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return raw_output.get("regions", [])


class MockAdaptedVqaModel(SpecialistModel):
    """
    Mock Remote-Sensing Adapted VQA Model (satquery-rs-v1) for CI / Unit Testing.
    Provides verified BigEarthNet CORINE terminology and adapter metadata.
    """
    name = "satquery-rs-v1"
    version = "1.0.0"
    task = "visual_question_answering"
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]

    def __init__(self):
        self._is_loaded = False
        self.is_adapted = True
        self.adapter_id = "satquery-rs-v1"
        self.adapter_type = "lora"
        self.dataset_provenance = "BigEarthNet v2.0"
        self.base_model_id = "Salesforce/blip-vqa-base"

    def load(self, device: str = "cpu") -> None:
        self._is_loaded = True

    def validate_input(self, image_bytes: bytes, metadata: Dict[str, Any]) -> None:
        if not image_bytes:
            raise ValueError("Empty image data provided.")

    def preprocess(self, image_bytes: bytes, metadata: Dict[str, Any]) -> Image.Image:
        return RemoteSensingPreprocessor.read_and_normalize_bands(
            image_bytes=image_bytes,
            nodata=metadata.get("nodata")
        )

    def predict(self, processed_input: Any, query: Optional[str] = None) -> Dict[str, Any]:
        q = (query or "").lower().strip()

        if "water" in q or "wetland" in q or "river" in q or "lake" in q:
            ans = "Yes, water bodies and inland wetlands are present with low near-infrared reflectance."
            conf = 0.94
        elif "building" in q or "urban" in q or "infrastructure" in q or "structure" in q:
            if "not" in q or "without" in q:
                ans = "No, the image contains natural vegetative cover with no dense urban structures."
            else:
                ans = "Urban fabric and industrial or commercial units with distinct geometric rooftop footprints."
            conf = 0.93
        elif "agricultural" in q or "crop" in q or "arable" in q or "pasture" in q or "rural" in q:
            ans = "Arable land and complex cultivation patterns with active crop boundaries and pastures."
            conf = 0.91
        elif "forest" in q or "tree" in q or "canopy" in q or "vegetat" in q:
            ans = "Broad-leaved forest and mixed forest canopy exhibiting high vegetation vigor."
            conf = 0.92
        else:
            ans = "Remote-sensing land cover characterized by complex cultivation patterns and natural vegetation."
            conf = 0.88

        return {
            "answer": ans,
            "confidence_score": conf,
            "confidence_method": "domain_adapted_vlm_posterior",
            "is_adapted": True,
            "adapter_id": self.adapter_id,
            "mock": True,
        }

    def postprocess(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "answer": raw_output.get("answer", ""),
            "adapter_metadata": {
                "adapter_id": self.adapter_id,
                "is_adapted": True,
                "dataset": "BigEarthNet v2.0",
            }
        }

    def confidence(self, raw_output: Any) -> Dict[str, Any]:
        return {
            "score": raw_output.get("confidence_score", 0.90),
            "method": raw_output.get("confidence_method", "domain_adapted_vlm_posterior"),
        }

    def evidence(self, raw_output: Any) -> List[Dict[str, Any]]:
        return [
            {
                "type": "rs_adapted_prediction",
                "adapter_id": self.adapter_id,
                "dataset": "BigEarthNet v2.0",
            }
        ]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "task": self.task,
            "is_adapted": True,
            "adapter_type": "lora",
            "base_model": "Salesforce/blip-vqa-base",
            "dataset_provenance": "BigEarthNet v2.0",
            "mock": True,
        }



