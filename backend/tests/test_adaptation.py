"""Tests for Phase 7 Remote-Sensing Adaptation & Domain Fine-Tuning.

Verifies:
1. BigEarthNet metadata definitions (CORINE 19, Sentinel-1/2 bands).
2. BigEarthNet validation and quarantine logic.
3. Deterministic 70/15/15 split generation with zero data leakage.
4. Optical and SAR preprocessing (percentile stretching, dB scaling, prompt normalization).
5. Self-contained LoRA engine (LoRALinear forward pass, freezing base params, state dict save/load).
6. Model registry resolution of satquery-rs-v1 and task alias resolution.
7. VRSBench and RSVQA benchmark metric calculation.
8. API endpoints: /models, /models/{id}, /models/{id}/metrics, /vqa, /agent/analyze.
"""

import io
import json
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
import torch
import torch.nn as nn
from pathlib import Path

from backend.training.datasets.bigearthnet.metadata import (
    BIGEARTHNET_19_CLASSES,
    SENTINEL2_BANDS,
    SENTINEL1_CHANNELS,
    BAND_PROJECTIONS,
)
from backend.training.datasets.bigearthnet.validation import BigEarthNetValidator
from backend.training.datasets.bigearthnet.splits import DatasetSplitter
from backend.training.preprocessing.optical import OpticalPreprocessor
from backend.training.preprocessing.sar import SARPreprocessor
from backend.training.preprocessing.text import RSTextPreprocessor
from backend.training.peft_adapter import LoRALinear, LoRAManager
from app.ai.registry import ModelRegistry
from app.ai.runtime import ModelRuntime
from app.ai.models.mock import MockAdaptedVqaModel
from evaluation.vrsbench.metrics import evaluate_predictions, compute_exact_match, compute_token_f1


def create_test_geotiff() -> bytes:
    """Creates an in-memory valid 3-band GeoTIFF for testing."""
    buf = io.BytesIO()
    data = (np.random.rand(3, 100, 100) * 2000).astype(np.uint16)
    transform = from_origin(600000, 3100000, 10, 10)

    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=100,
        width=100,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. BigEarthNet Metadata Tests
# ---------------------------------------------------------------------------
def test_bigearthnet_metadata():
    """Verify CORINE 19 classes and sensor band specifications."""
    assert len(BIGEARTHNET_19_CLASSES) == 19
    assert len(SENTINEL2_BANDS) == 12
    assert "B02" in SENTINEL2_BANDS and "B04" in SENTINEL2_BANDS and "B08" in SENTINEL2_BANDS
    assert "VV" in SENTINEL1_CHANNELS and "VH" in SENTINEL1_CHANNELS
    assert "RGB" in BAND_PROJECTIONS

    assert BIGEARTHNET_19_CLASSES[0] == "Urban fabric"
    assert "Water bodies" in BIGEARTHNET_19_CLASSES


# ---------------------------------------------------------------------------
# 2. BigEarthNet Validation & Quarantine Tests
# ---------------------------------------------------------------------------
def test_bigearthnet_validation():
    """Verify validator detects invalid labels, missing identifiers, and valid records."""
    validator = BigEarthNetValidator()

    # Valid record
    valid_sample = {
        "sample_id": "S2A_MSIL2A_20170613T101031_N0205_R022_T32ULD_82_54",
        "labels": ["Urban fabric", "Water bodies"],
        "optical_path": "path/to/optical.tif",
        "sar_path": "path/to/sar.tif",
        "metadata": {"dimensions": [120, 120]},
    }
    rec = validator.validate_sample(valid_sample, check_files_exist=False)
    assert rec.is_valid
    assert len(rec.error_reasons) == 0

    # Invalid record with unknown land cover label
    invalid_sample = {
        "sample_id": "test_001",
        "labels": ["Alien Landscape"],
        "optical_path": "path/to/optical.tif",
    }
    rec_inv = validator.validate_sample(invalid_sample, check_files_exist=False)
    assert not rec_inv.is_valid
    assert any("Unrecognized land cover" in err for err in rec_inv.error_reasons)

    # Empty labels should fail
    empty_labels = {
        "sample_id": "test_002",
        "labels": [],
        "optical_path": "path/to/optical.tif",
    }
    rec_empty = validator.validate_sample(empty_labels, check_files_exist=False)
    assert not rec_empty.is_valid

    # Batch dataset validation
    batch_result = validator.validate_dataset([valid_sample, invalid_sample])
    report = batch_result["report"]
    assert report["total_samples"] == 2
    assert report["valid_samples"] == 1
    assert report["invalid_samples"] == 1


# ---------------------------------------------------------------------------
# 3. Deterministic Splits & Zero Data Leakage
# ---------------------------------------------------------------------------
def test_deterministic_splits_and_leakage():
    """Verify deterministic splitting and zero overlap between splits."""
    samples = [
        {
            "sample_id": f"S2A_MSIL2A_20170613T101031_N0205_R022_T32ULD_{i:02d}_{i:02d}",
            "labels": ["Urban fabric"],
        }
        for i in range(40)
    ] + [
        {
            "sample_id": f"S2A_MSIL2A_20170613T101031_N0205_R022_T33UUP_{i:02d}_{i:02d}",
            "labels": ["Coniferous forest"],
        }
        for i in range(30)
    ] + [
        {
            "sample_id": f"S2A_MSIL2A_20170613T101031_N0205_R022_T30TYN_{i:02d}_{i:02d}",
            "labels": ["Water bodies"],
        }
        for i in range(30)
    ]

    splits = DatasetSplitter.split(
        samples, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42, group_by_prefix=False
    )
    assert "train" in splits and "validation" in splits and "test" in splits
    assert len(splits["train"]) > 0
    assert len(splits["validation"]) > 0
    assert len(splits["test"]) > 0
    assert len(splits["train"]) + len(splits["validation"]) + len(splits["test"]) == 100

    # Verify zero leakage
    train_ids = {s["sample_id"] for s in splits["train"]}
    val_ids = {s["sample_id"] for s in splits["validation"]}
    test_ids = {s["sample_id"] for s in splits["test"]}

    assert train_ids.isdisjoint(val_ids), "Leakage between train and validation!"
    assert train_ids.isdisjoint(test_ids), "Leakage between train and test!"
    assert val_ids.isdisjoint(test_ids), "Leakage between validation and test!"

    # Calling verify_zero_leakage should pass without raising
    DatasetSplitter.verify_zero_leakage(splits["train"], splits["validation"], splits["test"])


# ---------------------------------------------------------------------------
# 4. Preprocessing Tests (Optical & SAR)
# ---------------------------------------------------------------------------
def test_optical_and_sar_preprocessing():
    """Verify optical percentile stretching, band projection, SAR dB conversion, and text prompt cleaning."""
    # Synthetic optical band [120, 120]
    optical_data = np.random.randint(100, 4000, size=(120, 120), dtype=np.uint16)
    stretched = OpticalPreprocessor.percentile_stretch(optical_data)
    assert stretched.shape == (120, 120)
    assert stretched.dtype == np.uint8
    assert stretched.min() >= 0
    assert stretched.max() <= 255

    # Band projection to RGB PIL Image
    bands = {
        "B04": optical_data,
        "B03": (optical_data * 0.9).astype(np.uint16),
        "B02": (optical_data * 0.8).astype(np.uint16),
    }
    rgb_img = OpticalPreprocessor.project_bands(bands, projection_type="RGB")
    assert rgb_img.size == (120, 120)

    # SAR dB conversion
    sar_linear = np.random.uniform(0.01, 10.0, size=(120, 120)).astype(np.float32)
    sar_db = SARPreprocessor.to_decibel(sar_linear)
    assert sar_db.shape == (120, 120)

    sar_filtered = SARPreprocessor.speckle_filter_and_normalize(sar_linear)
    assert sar_filtered.dtype == np.uint8
    assert sar_filtered.min() >= 0
    assert sar_filtered.max() <= 255

    # SAR composite
    sar_composite = SARPreprocessor.compose_sar_composite({"VV": sar_linear, "VH": sar_linear * 0.5})
    assert sar_composite.size == (120, 120)

    # Text prompt & answer normalization
    prompt = RSTextPreprocessor.format_query("Is there water")
    assert prompt == "Satellite image analysis: Is there water?"
    assert RSTextPreprocessor.normalize_answer("  Urban Fabric.  ") == "urban fabric"


# ---------------------------------------------------------------------------
# 5. PEFT / LoRA Engine Tests
# ---------------------------------------------------------------------------
def test_peft_lora_engine(tmp_path):
    """Verify pure PyTorch LoRA forward pass, parameter freezing, and checkpoint save/load."""
    base_linear = nn.Linear(64, 32, bias=True)
    lora_linear = LoRALinear(base_linear, r=4, alpha=8, dropout=0.0)

    # Check forward pass
    x = torch.randn(2, 64)
    out = lora_linear(x)
    assert out.shape == (2, 32)

    # Initially LoRA B is zeros, so out should match base_linear(x) exactly
    base_out = base_linear(x)
    assert torch.allclose(out, base_out, atol=1e-5)

    # Test LoRAManager on a simple toy model
    class ToyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(32, 16)
            self.fc2 = nn.Linear(16, 8)

        def forward(self, x):
            return self.fc2(torch.relu(self.fc1(x)))

    toy = ToyModel()
    toy, stats = LoRAManager.apply_lora(toy, target_submodules=["fc1", "fc2"], r=4, alpha=8)
    assert stats["injected_layers"] == 2

    # Verify base weights are frozen
    assert not toy.fc1.base_layer.weight.requires_grad
    assert not toy.fc2.base_layer.weight.requires_grad
    # Verify LoRA weights are trainable
    assert toy.fc1.lora_A.requires_grad
    assert toy.fc1.lora_B.requires_grad

    # Test saving and loading weights
    ckpt_dir = tmp_path / "lora_ckpt"
    LoRAManager.save_adapter(toy, ckpt_dir, config={"lora": {"r": 4, "alpha": 8}})
    assert (ckpt_dir / "adapter" / "adapter_model.bin").exists()
    assert (ckpt_dir / "adapter" / "adapter_config.json").exists()

    # Load weights into fresh model
    toy_fresh = ToyModel()
    toy_fresh, _ = LoRAManager.apply_lora(toy_fresh, target_submodules=["fc1", "fc2"], r=4, alpha=8)
    LoRAManager.load_adapter(toy_fresh, ckpt_dir)


# ---------------------------------------------------------------------------
# 6. Model Registry & Runtime Integration Tests
# ---------------------------------------------------------------------------
def test_model_registry_rs_adapted():
    """Verify satquery-rs-v1 is registered with correct metadata."""
    registry = ModelRegistry()
    mock_model = MockAdaptedVqaModel()
    registry.register(mock_model)

    model = registry.get("satquery-rs-v1")
    assert model is not None
    info = model.get_model_info()
    assert info["is_adapted"] is True
    assert info["base_model"] == "Salesforce/blip-vqa-base"
    assert "BigEarthNet" in info["dataset_provenance"]

    models_list = registry.list_models()
    matching = [m for m in models_list if m["name"] == "satquery-rs-v1"]
    assert len(matching) == 1
    assert matching[0]["is_adapted"] is True


def test_ai_runtime_adapted_preference(monkeypatch):
    """Verify ModelRuntime initializes with satquery-rs-v1 as default VQA model."""
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "AI_USE_MOCK", True)
    registry = ModelRegistry()
    runtime = ModelRuntime(registry=registry)
    runtime.initialize_models()
    vqa_model = runtime.get_model_for_task("vqa")
    assert vqa_model is not None
    assert vqa_model.name == "satquery-rs-v1"


# ---------------------------------------------------------------------------
# 7. Benchmark Evaluation Metrics Tests
# ---------------------------------------------------------------------------
def test_benchmark_metrics():
    """Verify metric computation for VRSBench and RSVQA."""
    preds = ["urban fabric", "coniferous forest", "water bodies"]
    refs = ["urban fabric", "broad-leaved forest", "water bodies"]
    metrics = evaluate_predictions(preds, refs)
    assert pytest.approx(metrics["exact_match"], 0.01) == 2.0 / 3.0
    assert metrics["token_f1"] > 0.6
    assert compute_exact_match("Urban Fabric", "urban fabric") == 1.0
    assert compute_token_f1("mixed forest", "coniferous forest") > 0.0


# ---------------------------------------------------------------------------
# 8. API Endpoint Tests
# ---------------------------------------------------------------------------
def test_api_models_endpoints(client):
    """Verify /api/v1/analysis/models exposes adapted model and metrics."""
    res = client.get("/api/v1/analysis/models")
    assert res.status_code == 200
    data = res.json()
    model_names = [m["name"] for m in data]
    assert "satquery-rs-v1" in model_names

    # Check specific model details
    res_model = client.get("/api/v1/analysis/models/satquery-rs-v1")
    assert res_model.status_code == 200
    model_data = res_model.json()
    assert model_data["is_adapted"] is True
    assert model_data["dataset_provenance"] == "BigEarthNet v2.0"

    # Check metrics
    res_metrics = client.get("/api/v1/analysis/models/satquery-rs-v1/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert metrics_data["model_name"] == "satquery-rs-v1"
    assert "vrsbench" in metrics_data["benchmarks"]
    assert "rsvqa" in metrics_data["benchmarks"]


def test_api_vqa_adapted_response(client):
    """Verify /api/v1/analysis/vqa returns is_adapted flag and adapter metadata."""
    file_bytes = create_test_geotiff()
    files = {"file": ("test_satellite.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    res = client.post(
        "/api/v1/analysis/vqa",
        json={"image_id": image_id, "query": "What land cover is visible?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_adapted"] is True
    assert data["adapter_metadata"] is not None
    assert data["adapter_metadata"]["adapter_id"] == "satquery-rs-v1"


def test_api_agent_vqa_adapted_selection(client):
    """Verify agent routes query to satquery-rs-v1 and marks trace with adaptation."""
    file_bytes = create_test_geotiff()
    files = {"file": ("test_satellite.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    res = client.post(
        "/api/v1/agent/analyze",
        json={"image_ids": [image_id], "query": "What type of land cover is shown in this scene?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["task"] in ["VISUAL_QUESTION_ANSWERING", "vqa", "visual_question_answering"]
    assert data["is_adapted"] is True
    assert data["adapter_id"] == "satquery-rs-v1"

    # Verify execution trace contains adaptation information
    trace_events = [e["event_type"] for e in data["trace"]["events"]]
    assert "TOOL_EXECUTED" in trace_events
