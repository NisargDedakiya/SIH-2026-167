"""
Comprehensive Unit and Integration Tests for SatQuery Bi-Temporal Change Intelligence (Phase 5).
Validates:
1. Spatial overlap calculation and boundary compatibility.
2. Temporal ordering and pair validation (T1 < T2).
3. Non-destructive co-registration and resampling.
4. Siamese feature difference inference and thresholding.
5. Connected-component change region extraction with pixel and native CRS bounds.
6. Factual change description and Change VQA question answering.
7. Agentic query routing (invariant: multi-image change queries route to CHANGE_ANALYSIS, never VQA).
8. End-to-end API endpoints (/api/v1/temporal/* and /api/v1/agent/analyze).
"""

import datetime
import io
import uuid
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.temporal.compatibility import SpatialCompatibilityChecker
from app.temporal.validator import BiTemporalValidator
from app.temporal.alignment import AlignmentEngine
from app.temporal.change_map import ChangeMap
from app.temporal.regions import ChangeRegionExtractor
from app.temporal.description import ChangeDescriptionEngine
from app.temporal.change_vqa import ChangeVQAEngine
from app.temporal.schemas import (
    BiTemporalPairCreate,
    ChangeAnalysisRequest,
    ChangeRegion,
)
from app.ai.models.mock import MockChangeDetectionModel
from app.agent.classifier import QueryClassifier


class MockImageModel:
    """Lightweight test double for ImageModel."""
    def __init__(
        self,
        is_geospatial: bool = True,
        crs: str = "EPSG:32643",
        bounds_json: dict = None,
        width: int = 64,
        height: int = 64,
        acquisition_time: datetime.datetime = None,
        img_id: uuid.UUID = None,
        modality: str = "optical"
    ):
        self.id = img_id or uuid.uuid4()
        self.is_geospatial = is_geospatial
        self.crs = crs
        self.bounds_json = bounds_json or {"left": 500000.0, "bottom": 2999000.0, "right": 501000.0, "top": 3000000.0}
        self.width = width
        self.height = height
        self.acquisition_time = acquisition_time or datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        self.modality = modality
        self.band_count = 3

    @property
    def bounds(self):
        return self.bounds_json



def make_geotiff_bytes(origin_x=500000, origin_y=3000000, width=64, height=64, value_fill=1000) -> bytes:
    mem_buffer = io.BytesIO()
    data = np.full((3, height, width), value_fill, dtype=np.uint16)
    transform = from_origin(origin_x, origin_y, 10, 10)
    with rasterio.open(
        mem_buffer,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)
    return mem_buffer.getvalue()


# =========================================================================
# 1. Spatial Compatibility Tests
# =========================================================================

def test_spatial_compatibility_identical():
    img1 = MockImageModel()
    img2 = MockImageModel()
    result = SpatialCompatibilityChecker.check_spatial_compatibility(img1, img2)
    assert result["compatible"] is True
    assert result["overlap_ratio"] > 0.99


def test_spatial_compatibility_disjoint():
    img1 = MockImageModel(bounds_json={"left": 500000.0, "bottom": 2999000.0, "right": 501000.0, "top": 3000000.0})
    img2 = MockImageModel(bounds_json={"left": 700000.0, "bottom": 3200000.0, "right": 701000.0, "top": 3201000.0})
    result = SpatialCompatibilityChecker.check_spatial_compatibility(img1, img2)
    assert result["compatible"] is False
    assert result["overlap_ratio"] == 0.0


def test_spatial_compatibility_partial():
    img1 = MockImageModel(bounds_json={"left": 500000.0, "bottom": 2999000.0, "right": 501000.0, "top": 3000000.0})
    img2 = MockImageModel(bounds_json={"left": 500500.0, "bottom": 2999000.0, "right": 501500.0, "top": 3000000.0})
    result = SpatialCompatibilityChecker.check_spatial_compatibility(img1, img2)
    assert result["compatible"] is True
    assert 0.4 < result["overlap_ratio"] < 0.6


# =========================================================================
# 2. Bi-Temporal Validation Tests
# =========================================================================

def test_temporal_validation_valid():
    t1 = datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2024, 1, 15, tzinfo=datetime.timezone.utc)
    img1 = MockImageModel(acquisition_time=t1)
    img2 = MockImageModel(acquisition_time=t2)

    val = BiTemporalValidator.validate_pair(image_t1=img1, image_t2=img2)
    assert val.valid is True
    assert val.overlap_ratio > 0.99
    assert len(val.errors) == 0


def test_temporal_validation_inverted_time():
    t1 = datetime.datetime(2024, 1, 15, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2023, 1, 15, tzinfo=datetime.timezone.utc)
    img1 = MockImageModel(acquisition_time=t1)
    img2 = MockImageModel(acquisition_time=t2)

    val = BiTemporalValidator.validate_pair(image_t1=img1, image_t2=img2)
    assert val.valid is False
    assert any("temporal" in err.lower() or "later" in err.lower() for err in val.errors)



# =========================================================================
# 3. Non-Destructive Alignment Engine Tests
# =========================================================================

def test_alignment_engine_resample():
    t1_bytes = make_geotiff_bytes(origin_x=500000, origin_y=3000000, width=64, height=64)
    t2_bytes = make_geotiff_bytes(origin_x=500000, origin_y=3000000, width=32, height=32)
    img1 = MockImageModel(width=64, height=64)
    img2 = MockImageModel(width=32, height=32)

    t1_arr, t2_arr, meta = AlignmentEngine.align_pair(
        image_t1=img1,
        image_t2=img2,
        t1_bytes=t1_bytes,
        t2_bytes=t2_bytes
    )
    assert t1_arr.shape[:2] == (64, 64)
    assert t2_arr.shape[:2] == (64, 64)
    assert meta["target_width"] == 64


# =========================================================================
# 4. ChangeMap & Region Extraction Tests
# =========================================================================

def test_change_map_and_region_extraction():
    diff_scores = np.zeros((64, 64), dtype=np.float32)
    # Inject a 10x10 change block with confidence 0.85
    diff_scores[20:30, 20:30] = 0.85

    change_mask = (diff_scores > 0.35).astype(np.uint8)
    change_map = ChangeMap(change_mask=change_mask, change_scores=diff_scores, threshold=0.35)
    assert change_map.has_change is True
    assert change_map.change_percentage > 0.0

    overlay_bytes = change_map.to_png_bytes()
    assert len(overlay_bytes) > 0
    assert overlay_bytes.startswith(b"\x89PNG")

    # Extract regions using ChangeRegionExtractor
    regions = ChangeRegionExtractor.extract_regions(
        change_map=change_map,
        transform=[500000, 10, 0, 3000000, 0, -10],
        crs="EPSG:32643",
        min_region_size=20
    )
    assert len(regions) >= 1
    reg = regions[0]
    assert reg.pixel_geometry["x1"] == 20
    assert reg.pixel_geometry["y1"] == 20
    assert reg.pixel_area == 100
    assert reg.geo_geometry is not None


# =========================================================================
# 5. Change Description & Change VQA Tests
# =========================================================================

def test_change_description():
    diff_scores = np.zeros((64, 64), dtype=np.float32)
    diff_scores[10:30, 10:30] = 0.8
    change_mask = (diff_scores > 0.35).astype(np.uint8)
    change_map = ChangeMap(change_mask=change_mask, change_scores=diff_scores, threshold=0.35)

    regions = [
        ChangeRegion(
            region_id="reg-1",
            label="detected change region #1",
            bbox=[0.15, 0.15, 0.45, 0.45],
            pixel_geometry={"x1": 10, "y1": 10, "x2": 30, "y2": 30, "width": 20, "height": 20},
            geo_geometry=None,
            pixel_area=400,
            relative_area=0.097,
            confidence=0.88,
        )
    ]

    desc = ChangeDescriptionEngine.generate_description(change_map, regions, query="Describe construction changes")
    assert "changed" in desc.lower() or "structure" in desc.lower() or "built-up" in desc.lower()


def test_change_vqa():
    diff_scores = np.zeros((64, 64), dtype=np.float32)
    diff_scores[5:25, 5:25] = 0.85
    change_mask = (diff_scores > 0.35).astype(np.uint8)
    change_map = ChangeMap(change_mask=change_mask, change_scores=diff_scores, threshold=0.35)

    regions = [
        ChangeRegion(
            region_id="reg-1",
            label="Urban Expansion",
            bbox=[0.1, 0.1, 0.4, 0.4],
            pixel_geometry={"x1": 5, "y1": 5, "x2": 25, "y2": 25, "width": 20, "height": 20},
            geo_geometry=None,
            pixel_area=400,
            relative_area=0.097,
            confidence=0.9,
        )
    ]
    res = ChangeVQAEngine.answer_question(
        query="Did urban development increase between the two dates?",
        change_map=change_map,
        regions=regions,
    )
    ans = res["answer"]
    assert "yes" in ans.lower()
    assert "built-up" in ans.lower() or "urban" in ans.lower()


# =========================================================================
# 6. Model Adapter & AI Runtime Tests
# =========================================================================

def test_mock_change_detection_model():
    model = MockChangeDetectionModel()
    processed_input = {
        "t1": np.zeros((64, 64, 3), dtype=np.uint8),
        "t2": np.zeros((64, 64, 3), dtype=np.uint8),
    }

    raw = model.predict(processed_input, query="Did construction increase?")
    assert raw["change_mask"].shape == (64, 64)
    assert raw["change_scores"].shape == (64, 64)
    assert raw["confidence_score"] > 0.8


# =========================================================================
# 7. Agent Classification & Invariant Non-Fallback Routing Tests
# =========================================================================

def test_agent_routes_multi_image_to_change_analysis():
    # INVARIANT: Multi-image query about changes must route to CHANGE_ANALYSIS, never fallback to single-image VQA
    input_ctx = {"image_ids": ["img1", "img2"], "number_of_images": 2}

    queries = [
        "What changed between these two images?",
        "Did urban development increase over time?",
        "Show me vegetation loss between the two dates",
        "Compare the two satellite captures and describe differences",
    ]

    for q in queries:
        cls_result = QueryClassifier.classify(q, input_context=input_ctx)
        assert cls_result.intent == "CHANGE_ANALYSIS", f"Query '{q}' failed to route to CHANGE_ANALYSIS"


# =========================================================================
# 8. End-to-End API Integration Tests
# =========================================================================

def test_api_temporal_pair_and_analyze(client):
    # 1. Upload T1
    t1_bytes = make_geotiff_bytes(origin_x=500000, origin_y=3000000, value_fill=500)
    r1 = client.post(
        "/api/v1/images/upload",
        files={"file": ("t1.tif", t1_bytes, "image/tiff")},
        data={"acquisition_date": "2022-01-01T00:00:00Z"},
    )
    assert r1.status_code == 201
    img1_id = r1.json()["id"]

    # 2. Upload T2
    t2_bytes = make_geotiff_bytes(origin_x=500000, origin_y=3000000, value_fill=1200)
    r2 = client.post(
        "/api/v1/images/upload",
        files={"file": ("t2.tif", t2_bytes, "image/tiff")},
        data={"acquisition_date": "2023-01-01T00:00:00Z"},
    )
    assert r2.status_code == 201
    img2_id = r2.json()["id"]

    # 3. Create Pair
    pair_req = {
        "image_t1_id": img1_id,
        "image_t2_id": img2_id,
    }
    r_pair = client.post("/api/v1/temporal/pairs", json=pair_req)
    assert r_pair.status_code == 201
    pair_data = r_pair.json()
    pair_id = pair_data["pair_id"]
    assert pair_data["validation"]["valid"] is True
    assert pair_data["overlap_ratio"] > 0.99

    # 4. Get Pair
    r_get = client.get(f"/api/v1/temporal/pairs/{pair_id}")
    assert r_get.status_code == 200
    assert r_get.json()["pair_id"] == pair_id

    # 5. List Pairs
    r_list = client.get("/api/v1/temporal/pairs")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    # 6. Direct Change Analysis
    ana_req = {
        "pair_id": pair_id,
        "query": "What changed between these two dates?",
        "threshold": 0.35,
    }
    r_ana = client.post("/api/v1/temporal/analyze", json=ana_req)
    assert r_ana.status_code == 200
    ana_res = r_ana.json()
    assert ana_res["pair_id"] == pair_id
    assert "answer" in ana_res
    assert ana_res["change"]["threshold_used"] == 0.35
    assert len(ana_res["evidence"]) >= 1

    # 7. Agent Analysis with Pair / 2 Images
    agent_req = {
        "query": "What changed between these two dates?",
        "image_ids": [img1_id, img2_id],
    }
    r_agent = client.post("/api/v1/agent/analyze", json=agent_req)
    assert r_agent.status_code == 200
    agent_res = r_agent.json()
    assert agent_res["task"] == "CHANGE_ANALYSIS"
    assert agent_res["status"] == "completed"
    assert len(agent_res["tools"]) >= 1
    assert "change" in agent_res["tools"][0]["name"]
    assert agent_res["trace"] is not None
