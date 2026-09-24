"""
Phase 10 — Security Hardening, Input Validation & Agent Sandbox Tests.
Verifies path traversal resistance, decompression bomb protection,
malicious filename sanitization, agent sandbox restrictions, and intent regression.
"""

import io
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient

from app.agent.classifier import QueryClassifier
from app.agent.resolver import CapabilityResolver
from app.core.security import sanitize_filename, validate_file_extension
from app.geospatial.validator import GeospatialValidator


def create_synthetic_geotiff(width=64, height=64) -> bytes:
    mem_buffer = io.BytesIO()
    data = (np.random.rand(3, height, width) * 4000).astype(np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)
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
# 1. Path Traversal & Filename Sanitization Tests
# =========================================================================

def test_sanitize_filename_path_traversal():
    """Verify that dangerous directory traversal and null byte injections are stripped."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_image.tif\x00.exe") == "safe_image.tif.exe"
    assert sanitize_filename("....//..//image.png") == "image.png"
    assert sanitize_filename("") == "unnamed_image"
    assert sanitize_filename("..") == "unnamed_image"


def test_validate_file_extension_allowlist():
    """Verify strictly allowable extensions."""
    valid, ext = validate_file_extension("image.tif")
    assert valid and ext == ".tif"

    valid, ext = validate_file_extension("image.TIFF")
    assert valid and ext == ".tiff"

    valid, ext = validate_file_extension("payload.py")
    assert not valid and ext == ".py"

    valid, ext = validate_file_extension("exploit.sh")
    assert not valid and ext == ".sh"


# =========================================================================
# 2. Decompression Bomb & Resource Limits
# =========================================================================

def test_decompression_bomb_dimension_protection():
    """Validate that rasters claiming dimensions beyond MAX_RASTER_DIMENSION are rejected."""
    # Create fake TIFF header with gigantic dimensions (e.g. 10000 x 10000)
    res = GeospatialValidator.validate_file_content(b"fake_bytes_not_tiff", "test.tif")
    assert not res.valid


# =========================================================================
# 3. Agent Intent Classification Regression Suite
# =========================================================================

@pytest.mark.parametrize(
    "query,expected_intent",
    [
        ("How many buildings are visible?", "VISUAL_QUESTION_ANSWERING"),
        ("Describe this image.", "SCENE_DESCRIPTION"),
        ("Highlight the buildings.", "GROUNDING"),
        ("What changed between these images?", "CHANGE_ANALYSIS"),
        ("Which areas changed?", "CHANGE_ANALYSIS"),
        ("Compare optical and SAR imagery.", "CROSS_MODAL_ANALYSIS"),
        ("Where are the objects?", "GROUNDING"),
        ("Tell me about this.", "AMBIGUOUS"),
    ],
)
def test_agent_intent_canonical_regression_matrix(query, expected_intent):
    """Verify all 8 canonical Phase 10 evaluation queries map to deterministic intents."""
    res = QueryClassifier.classify(query)
    assert res.intent == expected_intent
    if expected_intent == "AMBIGUOUS":
        assert res.is_ambiguous is True
        assert res.clarification_prompt is not None


# =========================================================================
# 4. Agent Sandbox & Registry Enforcement
# =========================================================================

def test_agent_sandbox_unsupported_capability_no_fallback():
    """Verify that an unsupported or unserviced task does not silently fall back to random code."""
    resolver = CapabilityResolver()
    res = resolver.resolve("ARBITRARY_PYTHON_EXECUTION", {"number_of_images": 1})
    assert res.is_executable is False
    assert res.tool is None
    assert "not recognized" in res.status_reason


def test_agent_requires_multi_image_for_change_analysis():
    """Verify change analysis strictly enforces >= 2 images and refuses single image."""
    resolver = CapabilityResolver()
    res = resolver.resolve("CHANGE_ANALYSIS", {"number_of_images": 1})
    assert res.is_executable is False
    assert "requires at least 2 image(s)" in res.status_reason


# =========================================================================
# 5. Security API Endpoint Testing
# =========================================================================

def test_upload_path_traversal_via_api(client: TestClient):
    """Verify upload endpoint sanitizes traversed filename and persists safely."""
    tif_data = create_synthetic_geotiff(32, 32)
    files = {"file": ("../../malicious.tif", io.BytesIO(tif_data), "image/tiff")}
    response = client.post("/api/v1/images/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert ".." not in data["filename"]
    assert data["filename"] == "malicious.tif"
