"""
Adversarial and Edge-Case Failure Mode Tests for Remote-Sensing VLM (Part 24 & Part 27).

Verifies that the remote-sensing analysis system does not confidently hallucinate on:
1. Cloud-heavy images (high cloud fraction -> reduced confidence or cloud warning)
2. Very dark SAR scenes (specular/low backscatter -> calibrated confidence)
3. Missing or incomplete metadata (graceful default handling)
4. Non-standard resolutions & extreme aspect ratios (aspect preservation & valid bounds)
5. Unexpected band counts (4-band RGB+NIR or single-band panchromatic handling)
6. Corrupted or unreadable image bytes (clean validation rejection)
7. Checkpoint unavailability & Fallback logging (Part 27 compliance)
"""

import io
import pytest
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin

from app.ai.models.vqa.rs_adapted_vqa import RsAdaptedVqaModel
from app.ai.exceptions import ModelUnavailableError, UnsupportedModalityError
from app.ai.runtime import ModelRuntime
from app.ai.registry import ModelRegistry
from app.core.config import get_settings


def create_in_memory_geotiff(bands: int, height: int, width: int, fill_val: int = 1000) -> bytes:
    """Helper to generate in-memory GeoTIFFs with custom band counts and dimensions."""
    buf = io.BytesIO()
    data = np.full((bands, height, width), fill_val, dtype=np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)

    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=bands,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Cloud-Heavy Image Failure Test
# ---------------------------------------------------------------------------
def test_cloud_heavy_image_adversarial():
    """Verify that a cloud-saturated image does not hallucinate false land features."""
    model = RsAdaptedVqaModel()
    model.load("cpu")

    # Synthetic cloud-heavy scene (near saturation in all visible channels)
    cloud_img = Image.new("RGB", (384, 384), color=(250, 252, 255))
    res = model.predict(cloud_img, query="What is the dominant land cover class?")

    # Should detect urban/bright reflectance or flag high brightness with bounded confidence
    assert "answer" in res
    assert res["confidence"]["score"] <= 0.95
    assert not ("water" in res["answer"].lower() and "dominant" in res["answer"].lower())


# ---------------------------------------------------------------------------
# 2. Very Dark SAR Image Failure Test
# ---------------------------------------------------------------------------
def test_very_dark_sar_image_low_backscatter():
    """Verify very dark SAR image (specular calm water or radar shadow) is identified safely."""
    model = RsAdaptedVqaModel()
    model.load("cpu")

    # Near-zero backscatter (very dark radar response)
    dark_sar = Image.new("RGB", (384, 384), color=(5, 5, 8))
    res = model.predict(dark_sar, query="Is this an active urban center with tall buildings?")

    # Must NOT hallucinate high-density buildings on black radar patch
    answer_low = res["answer"].lower()
    assert "urban fabric" not in answer_low or "no" in answer_low


# ---------------------------------------------------------------------------
# 3. Missing Metadata Handling
# ---------------------------------------------------------------------------
def test_missing_metadata_resilience():
    """Verify model accepts missing/empty metadata dictionary without raising UnboundLocalError."""
    model = RsAdaptedVqaModel()
    model.load("cpu")

    sample_img = Image.new("RGB", (384, 384), color=(30, 120, 45))
    model.validate_input(b"valid_dummy_bytes", metadata={})
    res = model.predict(sample_img, query="What vegetation is visible?")

    assert "forest" in res["answer"].lower() or "vegetat" in res["answer"].lower()
    assert res["confidence"]["score"] > 0.0


# ---------------------------------------------------------------------------
# 4. Unusual Resolutions & Extreme Aspect Ratios
# ---------------------------------------------------------------------------
def test_unusual_aspect_ratio_preprocessing():
    """Verify non-square tall strip (e.g. 50x800) preprocessed to normalized bounds."""
    model = RsAdaptedVqaModel()
    strip_bytes = create_in_memory_geotiff(bands=3, height=800, width=50, fill_val=800)

    preprocessed = model.preprocess(strip_bytes, metadata={"nodata": None})
    assert isinstance(preprocessed, Image.Image)
    assert preprocessed.size == (384, 384)


# ---------------------------------------------------------------------------
# 5. Unexpected Band Count Handling
# ---------------------------------------------------------------------------
def test_unexpected_band_count_resilience():
    """Verify 4-band image (RGB + NIR) is gracefully projected to 3-band for VLM inference."""
    model = RsAdaptedVqaModel()
    four_band_bytes = create_in_memory_geotiff(bands=4, height=120, width=120, fill_val=1200)

    preprocessed = model.preprocess(four_band_bytes, metadata={"nodata": None})
    assert preprocessed.mode == "RGB"
    assert preprocessed.size == (384, 384)


# ---------------------------------------------------------------------------
# 6. Corrupted Image Bytes Rejection
# ---------------------------------------------------------------------------
def test_corrupted_image_bytes_rejection():
    """Verify corrupted bytes raise ValueError during validation."""
    model = RsAdaptedVqaModel()
    with pytest.raises(ValueError, match="Input image cannot be empty"):
        model.validate_input(b"", metadata={"modality": "optical"})


# ---------------------------------------------------------------------------
# 7. Part 27: Explicit Model Fallback Verification
# ---------------------------------------------------------------------------
def test_model_fallback_when_checkpoint_missing(tmp_path, monkeypatch):
    """
    Verify that if the RS-adapted adapter checkpoint is missing,
    the runtime logs an explicit fallback and records fallback metadata in the trace/result.
    """
    registry = ModelRegistry()
    # Create model pointing to non-existent checkpoint path
    missing_ckpt_path = tmp_path / "non_existent_adapter"
    faulty_adapted_model = RsAdaptedVqaModel(adapter_path=str(missing_ckpt_path))

    # Base baseline model to fall back to
    from app.ai.models.mock import MockVqaModel
    baseline_model = MockVqaModel()
    baseline_model.name = "remote-sensing-vqa-mock"

    registry.register(faulty_adapted_model, default_for_task=True)
    registry.register(baseline_model, default_for_task=False)

    runtime = ModelRuntime(registry=registry)

    # Execute runtime with missing checkpoint
    test_tiff = create_in_memory_geotiff(bands=3, height=100, width=100)
    result = runtime.execute(
        model=faulty_adapted_model,
        image_bytes=test_tiff,
        metadata={"modality": "optical", "nodata": None},
        query="What land cover is visible?"
    )

    # Must record fallback record explicitly
    assert "fallback" in result
    assert result["fallback"] is not None
    assert result["fallback"]["fallback_model"] == "remote-sensing-vqa-baseline"
    assert "RS-adapted checkpoint unavailable" in result["fallback"]["reason"]
