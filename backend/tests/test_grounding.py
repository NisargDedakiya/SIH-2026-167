"""
Unit and Integration tests for SatQuery Grounding & Visual Evidence Engine (Phase 4).
Tests coordinate reprojection, CRS bounding, visual overlay rendering, crop generation,
specialist model execution, and Agent grounding routing across all acceptance scenarios.
"""

import io
import uuid
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from PIL import Image
from fastapi.testclient import TestClient

from app.agent.classifier import QueryClassifier
from app.agent.controller import AgentController
from app.agent.resolver import CapabilityResolver
from app.ai.models.mock import MockGroundingModel
from app.evidence.geometry import pixel_bbox_to_geo_bounds, rescale_normalized_to_pixel
from app.evidence.overlay import render_evidence_overlay, render_region_crop
from app.tools.grounding import SingleImageGroundingTool
from app.tools.registry import get_tool_registry


def create_synthetic_geotiff_bytes() -> bytes:
    mem_buffer = io.BytesIO()
    data = (np.random.rand(3, 64, 64) * 4000).astype(np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)
    with rasterio.open(
        mem_buffer,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)
    return mem_buffer.getvalue()


# =========================================================================
# 1. Coordinate & Geometry Mapping Tests
# =========================================================================

def test_rescale_normalized_to_pixel():
    orig_w, orig_h = 4000, 3000
    norm_bbox = [0.25, 0.50, 0.75, 0.85]

    pixel_bbox = rescale_normalized_to_pixel(norm_bbox, orig_w, orig_h)
    assert pixel_bbox["x1"] == 1000
    assert pixel_bbox["y1"] == 1500
    assert pixel_bbox["x2"] == 3000
    assert pixel_bbox["y2"] == 2550
    assert pixel_bbox["width"] == 2000
    assert pixel_bbox["height"] == 1050


def test_pixel_to_geospatial_bounds_with_crs():
    # Affine transform: origin (500000, 3000000), resolution 10m x 10m
    aff = from_origin(500000, 3000000, 10, 10)
    crs = "EPSG:32643"
    pixel_bbox = {"x1": 10, "y1": 20, "x2": 30, "y2": 50, "width": 20, "height": 30}

    geo = pixel_bbox_to_geo_bounds(pixel_bbox, aff, crs)
    assert geo is not None
    assert geo["crs"] == "EPSG:32643"
    assert "bounds" in geo
    assert geo["bounds"]["min_x"] == 500100.0
    assert geo["bounds"]["max_x"] == 500300.0
    assert "polygon" in geo
    assert len(geo["polygon"]) == 5  # Closed ring


def test_pixel_to_geospatial_bounds_without_crs():
    pixel_bbox = {"x1": 10, "y1": 20, "x2": 30, "y2": 50, "width": 20, "height": 30}
    geo = pixel_bbox_to_geo_bounds(pixel_bbox, None, None)
    assert geo is None


# =========================================================================
# 2. Visual Overlay and Region Crop Rendering Tests
# =========================================================================

def test_render_evidence_overlay_and_crop():
    base_img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    regions = [
        {
            "label": "water body",
            "confidence": 0.92,
            "pixel_geometry": {"x1": 20, "y1": 30, "x2": 80, "y2": 90, "width": 60, "height": 60}
        },
        {
            "label": "building",
            "confidence": 0.85,
            "pixel_geometry": {"x1": 110, "y1": 120, "x2": 170, "y2": 180, "width": 60, "height": 60}
        }
    ]

    overlay_img = render_evidence_overlay(base_img, regions)
    assert overlay_img is not None
    assert overlay_img.size == (200, 200)

    crop_img = render_region_crop(base_img, regions[0]["pixel_geometry"])
    assert crop_img is not None
    assert crop_img.width > 0
    assert crop_img.height > 0


# =========================================================================
# 3. Grounding Specialist Model & Tool Tests
# =========================================================================

def test_mock_grounding_model_predictions():
    model = MockGroundingModel()
    geo_bytes = create_synthetic_geotiff_bytes()

    # Water query
    res_water = model.run(geo_bytes, metadata={}, query="Highlight the water body")
    assert res_water["task"] == "grounding"
    assert len(res_water["result"]["regions"]) >= 1
    assert "water" in res_water["result"]["regions"][0]["label"]
    assert res_water["confidence"]["score"] >= 0.85

    # Building query
    res_building = model.run(geo_bytes, metadata={}, query="Where are the buildings?")
    assert len(res_building["result"]["regions"]) >= 2
    assert "building" in res_building["result"]["regions"][0]["label"] or "structure" in res_building["result"]["regions"][0]["label"]


def test_grounding_tool_registry():
    reg = get_tool_registry()
    tool = reg.get("single_image_grounding")
    assert tool is not None
    assert tool.task == "GROUNDING"
    assert tool.status == "available"


# =========================================================================
# 4. Mandatory Phase 4 Acceptance Tests (Tests 1 - 5)
# =========================================================================

def test_acceptance_case_1_highlight_water_body(client: TestClient):
    """
    Test 1: 'Highlight the water body.'
    Expected: Task GROUNDING -> single_image_grounding tool -> water region -> visual evidence.
    """
    # Upload image
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_ground_water.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # Call agent
    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "Highlight the water body in this image.",
            "image_ids": [image_id]
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "completed"
    assert data["task"] == "GROUNDING"
    assert len(data["tools"]) >= 1
    assert data["tools"][0]["name"] == "single_image_grounding"
    assert "water" in data["answer"].lower()

    # Visual Evidence
    assert "evidence" in data
    assert len(data["evidence"]) >= 1
    ev = data["evidence"][0]
    assert "water" in ev["label"].lower()
    assert ev["confidence"] >= 0.85
    assert "pixel_geometry" in ev
    assert "geo_geometry" in ev
    assert ev["geo_geometry"] is not None  # Has CRS EPSG:32643
    assert ev["geo_geometry"]["crs"] == "EPSG:32643"
    assert ev["artifact_key"] is not None


def test_acceptance_case_2_where_are_buildings(client: TestClient):
    """
    Test 2: 'Where are the buildings?'
    Expected: Task GROUNDING -> building regions returned with spatial evidence.
    """
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_ground_buildings.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "Where are the buildings?",
            "image_ids": [image_id]
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "completed"
    assert data["task"] == "GROUNDING"
    assert data["tools"][0]["name"] == "single_image_grounding"
    assert len(data["evidence"]) >= 2
    assert "structure" in data["evidence"][0]["label"].lower() or "building" in data["evidence"][0]["label"].lower()


def test_acceptance_case_3_describe_scene_no_grounding(client: TestClient):
    """
    Test 3: 'Describe the scene.'
    Expected: Task SCENE_DESCRIPTION -> single_image_caption. Grounding must NOT be used.
    """
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_ground_caption.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "Describe the scene.",
            "image_ids": [image_id]
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "completed"
    assert data["task"] == "SCENE_DESCRIPTION"
    assert data["tools"][0]["name"] == "single_image_caption"
    assert data["tools"][0]["name"] != "single_image_grounding"


def test_acceptance_case_4_vqa_land_cover_no_grounding(client: TestClient):
    """
    Test 4: 'What type of land cover is visible?'
    Expected: Task VISUAL_QUESTION_ANSWERING -> single_image_vqa. Grounding must NOT be used.
    """
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_ground_vqa.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "What type of land cover is visible?",
            "image_ids": [image_id]
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "completed"
    assert data["task"] == "VISUAL_QUESTION_ANSWERING"
    assert data["tools"][0]["name"] == "single_image_vqa"


def test_acceptance_case_5_change_analysis_no_grounding(client: TestClient):
    """
    Test 5: 'What changed between these two images?'
    Expected: Task CHANGE_ANALYSIS -> not available yet. Must NOT route to grounding.
    """
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_ground_change.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "What changed between these two images?",
            "image_ids": [image_id]
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "unavailable"
    assert data["task"] == "CHANGE_ANALYSIS"
    assert data["tools"][0]["name"] != "single_image_grounding"


# =========================================================================
# 5. Direct Grounding & Evidence REST API Tests
# =========================================================================

def test_direct_grounding_and_evidence_endpoints(client: TestClient):
    """Verify POST /api/v1/analysis/grounding and GET /api/v1/analysis/{id}/evidence."""
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_direct_ground.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # 1. Run Grounding directly
    ground_res = client.post(
        "/api/v1/analysis/grounding",
        json={
            "image_id": image_id,
            "query": "water body"
        }
    )
    assert ground_res.status_code == 200
    data = ground_res.json()
    analysis_id = data["analysis_id"]
    assert data["task"] == "grounding"
    assert len(data["regions"]) >= 1

    # 2. Retrieve Evidence list
    ev_res = client.get(f"/api/v1/analysis/{analysis_id}/evidence")
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert len(ev_data) >= 1
    evidence_id = ev_data[0]["id"]

    # 3. Retrieve single Evidence by ID
    single_ev = client.get(f"/api/v1/analysis/evidence/{evidence_id}")
    assert single_ev.status_code == 200
    assert single_ev.json()["id"] == evidence_id

    # 4. Retrieve Artifact
    art_res = client.get(f"/api/v1/analysis/evidence/{evidence_id}/artifact")
    assert art_res.status_code == 200
    assert art_res.headers["content-type"] == "image/png"
    assert len(art_res.content) > 100
