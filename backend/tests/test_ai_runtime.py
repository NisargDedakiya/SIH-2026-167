"""
Unit tests for SatQuery AI Runtime, Model Registry, and Preprocessor (Phase 2).
"""

import io
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from app.ai.base import SpecialistModel
from app.ai.exceptions import ModelNotFoundError, UnsupportedModalityError
from app.ai.models.mock import MockCaptionModel, MockVqaModel
from app.ai.postprocessing import Postprocessor
from app.ai.preprocessing import RemoteSensingPreprocessor
from app.ai.registry import ModelRegistry
from app.ai.runtime import ModelRuntime


def create_synthetic_geotiff_bytes() -> bytes:
    """Helper creating a 3-band uint16 GeoTIFF in memory."""
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


def test_model_registry_registration_and_lookup():
    reg = ModelRegistry()
    vqa = MockVqaModel()
    caption = MockCaptionModel()

    reg.register(vqa)
    reg.register(caption)

    assert reg.get(vqa.name) == vqa
    assert reg.get_by_task("visual_question_answering") == vqa
    assert reg.get_by_task("image_captioning") == caption

    models_info = reg.list_models()
    assert len(models_info) == 2
    names = [m["name"] for m in models_info]
    assert vqa.name in names
    assert caption.name in names

    with pytest.raises(ModelNotFoundError):
        reg.get("non_existent_model")

    with pytest.raises(ModelNotFoundError):
        reg.get_by_task("unknown_task")


def test_remote_sensing_preprocessor_geotiff():
    geo_bytes = create_synthetic_geotiff_bytes()
    pil_img = RemoteSensingPreprocessor.read_and_normalize_bands(
        image_bytes=geo_bytes,
        target_size=(128, 128)
    )

    assert pil_img is not None
    assert pil_img.size == (128, 128)
    assert pil_img.mode == "RGB"


def test_mock_vqa_model_inference():
    geo_bytes = create_synthetic_geotiff_bytes()
    model = MockVqaModel()
    metadata = {"modality": "optical", "nodata": None}

    # Verify input validation
    model.validate_input(geo_bytes, metadata)

    # Test execution via run()
    res = model.run(
        image_bytes=geo_bytes,
        metadata=metadata,
        query="What land cover types are visible?"
    )

    assert res["task"] == "visual_question_answering"
    assert res["model"]["name"] == model.name
    assert "answer" in res["result"]
    assert "agricultural" in res["result"]["answer"].lower()
    assert res["confidence"]["score"] > 0.8
    assert isinstance(res["evidence"], list)


def test_mock_caption_model_inference():
    geo_bytes = create_synthetic_geotiff_bytes()
    model = MockCaptionModel()
    metadata = {"modality": "optical", "nodata": None}

    res = model.run(
        image_bytes=geo_bytes,
        metadata=metadata
    )

    assert res["task"] == "image_captioning"
    assert res["model"]["name"] == model.name
    assert "caption" in res["result"]
    assert len(res["result"]["caption"]) > 10
    assert res["confidence"]["score"] > 0.8


def test_model_runtime_device_and_execution():
    reg = ModelRegistry()
    vqa = MockVqaModel()
    reg.register(vqa)

    runtime = ModelRuntime(registry=reg)
    assert runtime.device in ["cpu", "cuda"]

    geo_bytes = create_synthetic_geotiff_bytes()
    metadata = {"modality": "optical"}

    result = runtime.execute(
        model=vqa,
        image_bytes=geo_bytes,
        metadata=metadata,
        query="What objects are visible?"
    )

    assert result["status"] if "status" in result else True
    assert "processing_time_ms" in result
    assert result["processing_time_ms"] >= 0


def test_postprocessor_formatting():
    vqa_out = Postprocessor.format_vqa_result(
        answer="Forest and water bodies.",
        confidence_score=0.91234,
        confidence_method="token_probability",
        processing_time_ms=150
    )
    assert vqa_out["task"] == "visual_question_answering"
    assert vqa_out["result"]["answer"] == "Forest and water bodies."
    assert vqa_out["confidence"]["score"] == 0.9123
    assert vqa_out["processing_time_ms"] == 150

    cap_out = Postprocessor.format_caption_result(
        caption="A rural scene.",
        confidence_score=0.8765,
        processing_time_ms=200
    )
    assert cap_out["task"] == "image_captioning"
    assert cap_out["result"]["caption"] == "A rural scene."
    assert cap_out["confidence"]["score"] == 0.8765
