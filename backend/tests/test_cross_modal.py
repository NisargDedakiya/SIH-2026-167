"""
Comprehensive Test Suite for Phase 6 — Optical + SAR Cross-Modal Intelligence.
Verifies pair validation, spatial compatibility, non-destructive alignment,
modality encoders, cross-modal fusion, task reasoning, agent routing, and API contracts.
"""

import io
import uuid
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.agent.classifier import QueryClassifier
from app.agent.controller import AgentController
from app.agent.planner import WorkflowPlanner
from app.agent.resolver import CapabilityResolver
from app.ai.models.cross_modal.fusion_model import CrossModalFusionModel
from app.ai.models.cross_modal.optical_encoder import OpticalEncoder
from app.ai.models.cross_modal.sar_encoder import SAREncoder
from app.ai.models.mock import MockCrossModalModel
from app.cross_modal.alignment import CrossModalAlignmentEngine
from app.cross_modal.compatibility import CrossModalSpatialCompatibility
from app.cross_modal.fusion import CrossModalFusion
from app.cross_modal.models import OpticalSARPairModel
from app.cross_modal.reasoning import CrossModalReasoningEngine
from app.cross_modal.schemas import OpticalSARPairCreate
from app.cross_modal.service import get_cross_modal_service
from app.cross_modal.validator import CrossModalValidator
from app.database.models import ImageModel
from app.main import app
from app.storage.object_store import get_object_store
from app.tools.registry import get_tool_registry

# client fixture is injected via conftest.py


def _create_synthetic_image_model(
    image_id: uuid.UUID,
    filename: str,
    modality: str,
    sensor: str,
    width: int = 128,
    height: int = 128,
    crs: str = "EPSG:32643",
    bounds: dict = None,
    band_count: int = 3
) -> ImageModel:
    if bounds is None:
        bounds = {"left": 500000.0, "bottom": 3000000.0, "right": 501280.0, "top": 3001280.0}
    return ImageModel(
        id=image_id,
        original_filename=filename,
        object_key=f"rasters/{image_id}/{filename}",
        mime_type="image/tiff",
        file_format="GeoTIFF",
        file_size=1024 * 50,
        checksum="abcd" * 16,
        width=width,
        height=height,
        band_count=band_count,
        dtype="uint8",
        crs=crs,
        epsg_code=32643 if "32643" in crs else None,
        resolution_x=10.0,
        resolution_y=10.0,
        bounds=bounds,
        transform=[10.0, 0.0, bounds["left"], 0.0, -10.0, bounds["top"]],
        sensor=sensor,
        modality=modality,
        is_geospatial=True,
        validation_status="valid",
    )


def _generate_synthetic_png_bytes(width: int = 64, height: int = 64, channels: int = 3, val: int = 120) -> bytes:
    if channels == 1:
        arr = np.full((height, width), val, dtype=np.uint8)
    else:
        arr = np.full((height, width, channels), val, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# =========================================================================
# 1. Modality Detection & Pair Validation Tests
# =========================================================================

def test_modality_detection_optical_and_sar():
    opt_img = _create_synthetic_image_model(
        uuid.uuid4(), "cartosat_2s_pan.tif", "optical", "Cartosat-2S"
    )
    sar_img = _create_synthetic_image_model(
        uuid.uuid4(), "risat_1a_cband_vv_vh.tif", "sar", "RISAT-1A", band_count=2
    )

    assert CrossModalValidator.detect_modality(opt_img) == "optical"
    assert CrossModalValidator.detect_modality(sar_img) == "sar"
    assert CrossModalValidator.detect_sar_polarization(sar_img) == "dual-pol"


def test_modality_detection_unknown_not_silently_optical():
    unk_img = _create_synthetic_image_model(
        uuid.uuid4(), "unlabeled_data.bin", "unknown", "CustomPlatformX"
    )
    assert CrossModalValidator.detect_modality(unk_img) == "unknown"


def test_cross_modal_pair_validator_success():
    opt_img = _create_synthetic_image_model(uuid.uuid4(), "cartosat_scene.tif", "optical", "Cartosat-2S")
    sar_img = _create_synthetic_image_model(uuid.uuid4(), "risat_scene_vv.tif", "sar", "RISAT-1A")

    res = CrossModalValidator.validate_pair(optical_image=opt_img, sar_image=sar_img)
    assert res.valid is True
    assert res.optical_valid is True
    assert res.sar_valid is True
    assert res.spatially_compatible is True
    assert res.overlap_ratio >= 0.50
    assert res.status_code == "VALID"


def test_cross_modal_pair_rejects_optical_plus_optical():
    opt1 = _create_synthetic_image_model(uuid.uuid4(), "cartosat_1.tif", "optical", "Cartosat-2S")
    opt2 = _create_synthetic_image_model(uuid.uuid4(), "sentinel2_optical.tif", "optical", "Sentinel-2")

    res = CrossModalValidator.validate_pair(optical_image=opt1, sar_image=opt2)
    assert res.valid is False
    assert res.status_code == "INVALID_SAR_MODALITY"
    assert "Temporal Analysis" in res.message or "Optical" in res.message


def test_cross_modal_pair_rejects_sar_plus_sar():
    sar1 = _create_synthetic_image_model(uuid.uuid4(), "risat_vv.tif", "sar", "RISAT-1A")
    sar2 = _create_synthetic_image_model(uuid.uuid4(), "sentinel1_vh.tif", "sar", "Sentinel-1")

    res = CrossModalValidator.validate_pair(optical_image=sar1, sar_image=sar2)
    assert res.valid is False
    assert res.status_code in ["INVALID_OPTICAL_MODALITY", "MODALITY_ORDER_SWAPPED"]


def test_cross_modal_pair_swapped_order_detected():
    sar1 = _create_synthetic_image_model(uuid.uuid4(), "risat_vv.tif", "sar", "RISAT-1A")
    opt2 = _create_synthetic_image_model(uuid.uuid4(), "cartosat_optical.tif", "optical", "Cartosat-2S")

    res = CrossModalValidator.validate_pair(optical_image=sar1, sar_image=opt2)
    assert res.valid is False
    assert res.status_code == "MODALITY_ORDER_SWAPPED"


# =========================================================================
# 2. Spatial Compatibility Tests
# =========================================================================

def test_spatial_compatibility_disjoint_bounds():
    opt_img = _create_synthetic_image_model(
        uuid.uuid4(), "opt.tif", "optical", "Cartosat",
        bounds={"left": 100.0, "bottom": 100.0, "right": 200.0, "top": 200.0}
    )
    sar_img = _create_synthetic_image_model(
        uuid.uuid4(), "sar.tif", "sar", "RISAT",
        bounds={"left": 900.0, "bottom": 900.0, "right": 950.0, "top": 950.0}
    )

    compat = CrossModalSpatialCompatibility.evaluate(opt_img, sar_img)
    assert compat["is_compatible"] is False
    assert compat["compatibility"] == "INCOMPATIBLE"
    assert compat["overlap_ratio"] == 0.0


def test_spatial_compatibility_partial_overlap():
    opt_img = _create_synthetic_image_model(
        uuid.uuid4(), "opt.tif", "optical", "Cartosat",
        bounds={"left": 100.0, "bottom": 100.0, "right": 300.0, "top": 300.0}
    )
    sar_img = _create_synthetic_image_model(
        uuid.uuid4(), "sar.tif", "sar", "RISAT",
        bounds={"left": 250.0, "bottom": 250.0, "right": 450.0, "top": 450.0}
    )

    compat = CrossModalSpatialCompatibility.evaluate(opt_img, sar_img)
    assert compat["is_compatible"] is True
    assert compat["compatibility"] == "PARTIALLY_COMPATIBLE"
    assert 0.0 < compat["overlap_ratio"] < 0.50


# =========================================================================
# 3. Preprocessing & Alignment Tests
# =========================================================================

def test_optical_preprocessing_multispectral():
    raw_4band = np.random.randint(0, 255, (64, 64, 4), dtype=np.uint8)
    processed = OpticalEncoder.preprocess(raw_4band)
    assert processed.shape == (64, 64, 4)
    assert processed.dtype == np.float32
    assert processed.max() <= 1.0


def test_sar_preprocessing_log_scale_not_blind_rgb():
    raw_sar = np.array([[10.0, 50.0], [500.0, 2000.0]], dtype=np.float32)
    processed = SAREncoder.preprocess(raw_sar, apply_db_scale=True)
    assert processed.shape == (2, 2, 1)
    assert processed.dtype == np.float32
    assert 0.0 <= processed.min() <= processed.max() <= 1.0


def test_cross_modal_alignment_resampling():
    opt_img = _create_synthetic_image_model(uuid.uuid4(), "opt.tif", "optical", "Cartosat", width=64, height=64)
    sar_img = _create_synthetic_image_model(uuid.uuid4(), "sar.tif", "sar", "RISAT", width=32, height=32)

    opt_bytes = _generate_synthetic_png_bytes(width=64, height=64, channels=3)
    sar_bytes = _generate_synthetic_png_bytes(width=32, height=32, channels=1)

    opt_arr, aligned_sar, meta = CrossModalAlignmentEngine.align(
        optical_image=opt_img,
        sar_image=sar_img,
        optical_bytes=opt_bytes,
        sar_bytes=sar_bytes,
    )

    assert opt_arr.shape[:2] == (64, 64)
    assert aligned_sar.shape[:2] == (64, 64)
    assert meta["target_width"] == 64
    assert meta["target_height"] == 64
    assert meta["quality"]["status"] == "VALID"
    assert meta["quality"]["quality_score"] is not None


# =========================================================================
# 4. Fusion, Reasoning & Disagreement Tests
# =========================================================================

def test_cross_modal_fusion_tensor():
    opt_feats = np.ones((32, 32, 3), dtype=np.float32)
    sar_feats = np.ones((32, 32, 1), dtype=np.float32)

    joint = CrossModalFusion.fuse_representations(opt_feats, sar_feats)
    assert joint.shape == (32, 32, 4)


def test_modality_contributions_reporting():
    opt_s, sar_s = CrossModalFusion.evaluate_modality_contributions(
        query="What can the SAR image reveal that the optical image does not?",
        optical_sensor="Cartosat-2S",
        sar_sensor="RISAT-1A",
        polarization="VV",
    )
    assert opt_s.modality == "optical"
    assert sar_s.modality == "sar"
    assert "visual" in opt_s.contribution.lower() or "spectral" in opt_s.contribution.lower()
    assert "radar" in sar_s.contribution.lower() or "roughness" in sar_s.contribution.lower()


def test_modality_disagreement_detection():
    # Test case 1: Agreement
    dis_agree = CrossModalFusion.evaluate_disagreement(
        query="Identify urban structures.",
        optical_signal={"detected": True, "confidence": 0.90},
        sar_signal={"detected": True, "confidence": 0.88},
    )
    assert dis_agree.agreement_status == "AGREEMENT"

    # Test case 2: Atmospheric cloud divergence
    dis_cloud = CrossModalFusion.evaluate_disagreement(
        query="Is there cloud cover over the vegetation?",
        optical_signal={"detected": False, "confidence": 0.60, "cloud_obscured": True},
        sar_signal={"detected": True, "confidence": 0.85},
    )
    assert dis_cloud.agreement_status == "PARTIAL_AGREEMENT"
    assert dis_cloud.disagreement_type == "ATMOSPHERIC_OBSCURATION"


def test_cross_modal_reasoning_water_query():
    res = CrossModalReasoningEngine.reason(
        query="Locate the water body using the complementary information from optical and SAR.",
        task="cross_modal_analysis",
        optical_meta={"sensor": "Cartosat-2S", "modality": "optical"},
        sar_meta={"sensor": "RISAT-1A", "modality": "sar", "polarization": "VV"},
        model_prediction={"confidence_score": 0.93, "regions": [{"label": "water", "bbox": [0.2, 0.2, 0.6, 0.6]}]},
        optical_shape=(100, 100),
    )
    assert "water" in res["answer"].lower()
    assert "specular" in res["answer"].lower() or "absorption" in res["answer"].lower()
    assert len(res["regions"]) == 1
    assert res["regions"][0].pixel_geometry["x1"] == 20


# =========================================================================
# 5. Agent Intent Routing & Tool Planning Tests
# =========================================================================

def test_agent_routes_optical_sar_to_cross_modal():
    q = "Analyze these optical and SAR images together."
    res = QueryClassifier.classify(q)
    assert res.intent == "CROSS_MODAL_ANALYSIS"

    resolver = CapabilityResolver()
    resolved = resolver.resolve(res.intent, {"number_of_images": 2, "query": q})
    assert resolved.is_executable is True
    assert resolved.tool.name == "optical_sar_analysis"


def test_agent_routes_sar_comparison_to_vqa_tool():
    q = "What does SAR reveal that is difficult to see in the optical image?"
    res = QueryClassifier.classify(q)
    assert res.intent == "CROSS_MODAL_ANALYSIS"

    resolver = CapabilityResolver()
    resolved = resolver.resolve(res.intent, {"number_of_images": 2, "query": q})
    assert resolved.is_executable is True
    assert resolved.tool.name == "optical_sar_vqa"


def test_agent_routes_cross_modal_grounding():
    q = "Highlight the urban regions supported by both images."
    res = QueryClassifier.classify(q)
    assert res.intent == "CROSS_MODAL_ANALYSIS"

    resolver = CapabilityResolver()
    resolved = resolver.resolve(res.intent, {"number_of_images": 2, "query": q})
    assert resolved.is_executable is True
    assert resolved.tool.name == "optical_sar_grounding"


def test_agent_distinguishes_temporal_from_cross_modal():
    q_temp = "What changed between 2026-01-01 and 2026-06-01?"
    res_temp = QueryClassifier.classify(q_temp, {"number_of_images": 2})
    assert res_temp.intent == "CHANGE_ANALYSIS"

    q_cm = "Combine SAR and optical evidence."
    res_cm = QueryClassifier.classify(q_cm, {"number_of_images": 2})
    assert res_cm.intent == "CROSS_MODAL_ANALYSIS"


def test_workflow_planner_cross_modal():
    planner = WorkflowPlanner()
    reg = get_tool_registry()
    tool = reg.get("optical_sar_analysis")

    pair_id = uuid.uuid4()
    plan = planner.create_plan(
        task="CROSS_MODAL_ANALYSIS",
        tool=tool,
        query="Analyze these images together.",
        input_context={"pair_id": str(pair_id)}
    )

    assert plan.task == "CROSS_MODAL_ANALYSIS"
    assert len(plan.steps) == 1
    assert plan.steps[0].tool == "optical_sar_analysis"
    assert plan.steps[0].parameters["pair_id"] == str(pair_id)


# =========================================================================
# 6. End-to-End API Integration Tests
# =========================================================================

def test_cross_modal_api_lifecycle(client):
    # 1. Upload optical image
    opt_bytes = _generate_synthetic_png_bytes(width=64, height=64, channels=3, val=150)
    opt_resp = client.post(
        "/api/v1/images/upload",
        files={"file": ("cartosat_optical_scene.png", opt_bytes, "image/png")}
    )
    assert opt_resp.status_code == 201
    opt_id = opt_resp.json()["id"]

    # 2. Upload SAR image
    sar_bytes = _generate_synthetic_png_bytes(width=64, height=64, channels=1, val=80)
    sar_resp = client.post(
        "/api/v1/images/upload",
        files={"file": ("risat_sar_cband_vv.png", sar_bytes, "image/png")}
    )
    assert sar_resp.status_code == 201
    sar_id = sar_resp.json()["id"]

    # 3. Create OpticalSARPair
    pair_req = {"optical_image_id": opt_id, "sar_image_id": sar_id}
    pair_resp = client.post("/api/v1/cross-modal/pairs", json=pair_req)
    assert pair_resp.status_code == 201
    pair_data = pair_resp.json()
    pair_id = pair_data["id"]
    assert pair_data["optical_modality"] == "optical"
    assert pair_data["sar_modality"] == "sar"
    assert pair_data["validation"]["valid"] is True

    # 4. Get pair
    get_resp = client.get(f"/api/v1/cross-modal/pairs/{pair_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == pair_id

    # 5. Validate pair endpoint
    val_resp = client.post(f"/api/v1/cross-modal/pairs/{pair_id}/validate")
    assert val_resp.status_code == 200
    assert val_resp.json()["valid"] is True

    # 6. Execute direct cross-modal analysis
    analyze_resp = client.post(
        "/api/v1/cross-modal/analyze",
        json={"pair_id": pair_id, "query": "Analyze these optical and SAR images together."}
    )
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert res["task"] == "CROSS_MODAL_ANALYSIS"
    assert "answer" in res
    assert "optical_summary" in res
    assert "sar_summary" in res
    assert "disagreement" in res
    assert len(res["regions"]) >= 1

    # 7. Execute VQA via /api/v1/analysis/cross-modal-vqa
    vqa_resp = client.post(
        "/api/v1/analysis/cross-modal-vqa",
        json={"pair_id": pair_id, "query": "What does SAR show that is difficult to see in the optical image?"}
    )
    assert vqa_resp.status_code == 200
    assert "answer" in vqa_resp.json()

    # 8. Execute grounding via /api/v1/analysis/cross-modal-grounding
    grounding_resp = client.post(
        "/api/v1/analysis/cross-modal-grounding",
        json={"pair_id": pair_id, "query": "Highlight the urban regions supported by both images."}
    )
    assert grounding_resp.status_code == 200
    g_res = grounding_resp.json()
    assert len(g_res["regions"]) >= 1
    assert "pixel_geometry" in g_res["regions"][0]

    # 9. Retrieve evidence via /api/v1/analysis/{analysis_id}/cross-modal-evidence
    analysis_id = g_res["analysis_id"]
    ev_resp = client.get(f"/api/v1/analysis/{analysis_id}/cross-modal-evidence")
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()) >= 1
