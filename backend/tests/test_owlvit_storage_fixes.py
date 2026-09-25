"""
Tests for OWL-ViT processor API compatibility and Object Storage consistency validation.
Covers:
1. OWL-ViT processor compatibility layer (post_process_grounded_object_detection, post_process_object_detection, image_processor fallback, unsupported error).
2. Grounding bounding box normalization (x1 < x2, y1 < y2, clamped [0, 1]).
3. ObjectStore exists() method and StorageObjectNotFoundError with IMAGE_OBJECT_MISSING code.
4. Storage integrity: DB record + object exists, object missing, preview missing.
5. Bi-temporal pair storage validation (valid vs INVALID_STORAGE).
6. Optical-SAR pair storage validation (valid vs INVALID_STORAGE).
"""

import os
import uuid
import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch

from app.ai.models.grounding.rs_grounding_adapter import RsGroundingModel, RSGroundingAdapter
from app.ai.exceptions import ModelExecutionError
from app.storage.object_store import LocalObjectStore
from app.storage.exceptions import StorageObjectNotFoundError
from app.services.image_service import ImageService
from app.temporal.service import TemporalPairService
from app.cross_modal.service import CrossModalPairService
from app.database.models import ImageModel, BiTemporalPairModel
from app.cross_modal.models import OpticalSARPairModel


# =========================================================================
# 1. OWL-ViT PROCESSOR API COMPATIBILITY TESTS
# =========================================================================

class DummyOutputs:
    def __init__(self):
        self.logits = torch.zeros((1, 5, 2))
        self.pred_boxes = torch.zeros((1, 5, 4))


def test_owlvit_postprocess_grounded_object_detection():
    """Verify primary branch: post_process_grounded_object_detection is called when available."""
    adapter = RsGroundingModel(model_id="google/owlvit-base-patch32")

    mock_proc = MagicMock()
    # Has post_process_grounded_object_detection
    mock_proc.post_process_grounded_object_detection.return_value = [
        {
            "boxes": torch.tensor([[10.0, 15.0, 40.0, 55.0]]),
            "scores": torch.tensor([0.88]),
            "labels": torch.tensor([0]),
            "text_labels": ["building"],
        }
    ]
    # Remove older methods to ensure grounded is chosen
    del mock_proc.post_process_object_detection

    adapter._processor = mock_proc
    outputs = DummyOutputs()
    target_sizes = torch.tensor([[100, 100]])
    text_queries = ["building"]

    regions = adapter._post_process_results(outputs, target_sizes, text_queries, threshold=0.1, orig_w=100, orig_h=100)

    mock_proc.post_process_grounded_object_detection.assert_called_once()
    assert len(regions) == 1
    assert regions[0]["label"] == "building"
    assert regions[0]["confidence"] == 0.88
    # Normalized coords [0, 1]
    assert regions[0]["bbox"] == [0.1, 0.15, 0.4, 0.55]


def test_owlvit_postprocess_legacy_object_detection():
    """Verify secondary branch: processor.post_process_object_detection is called when grounded is absent."""
    adapter = RsGroundingModel(model_id="google/owlvit-base-patch32")

    mock_proc = MagicMock(spec=["post_process_object_detection"])
    mock_proc.post_process_object_detection.return_value = [
        {
            "boxes": torch.tensor([[5.0, 5.0, 50.0, 50.0]]),
            "scores": torch.tensor([0.75]),
            "labels": torch.tensor([0]),
        }
    ]

    adapter._processor = mock_proc
    outputs = DummyOutputs()
    target_sizes = torch.tensor([[100, 100]])
    text_queries = ["building"]

    regions = adapter._post_process_results(outputs, target_sizes, text_queries, threshold=0.1, orig_w=100, orig_h=100)

    mock_proc.post_process_object_detection.assert_called_once()
    assert len(regions) == 1
    assert regions[0]["label"] == "building"
    assert regions[0]["confidence"] == 0.75
    assert regions[0]["bbox"] == [0.05, 0.05, 0.5, 0.5]


def test_owlvit_postprocess_image_processor_fallback():
    """Verify tertiary branch: processor.image_processor.post_process_object_detection."""
    adapter = RsGroundingModel(model_id="google/owlvit-base-patch32")

    mock_img_proc = MagicMock()
    mock_img_proc.post_process_object_detection.return_value = [
        {
            "boxes": torch.tensor([[20.0, 20.0, 80.0, 80.0]]),
            "scores": torch.tensor([0.92]),
            "labels": torch.tensor([0]),
        }
    ]

    mock_proc = MagicMock(spec=["image_processor"])
    mock_proc.image_processor = mock_img_proc

    adapter._processor = mock_proc
    outputs = DummyOutputs()
    target_sizes = torch.tensor([[100, 100]])
    text_queries = ["corridor"]

    regions = adapter._post_process_results(outputs, target_sizes, text_queries, threshold=0.1, orig_w=100, orig_h=100)

    mock_img_proc.post_process_object_detection.assert_called_once()
    assert len(regions) == 1
    assert regions[0]["label"] == "corridor"
    assert regions[0]["confidence"] == 0.92
    assert regions[0]["bbox"] == [0.2, 0.2, 0.8, 0.8]


def test_owlvit_postprocess_unsupported_raises_typed_error():
    """Verify that when no supported API exists, ModelExecutionError is raised with GROUNDING_POSTPROCESS_UNSUPPORTED."""
    adapter = RsGroundingModel(model_id="google/owlvit-base-patch32")

    mock_proc = MagicMock(spec=[])  # No methods at all
    adapter._processor = mock_proc
    outputs = DummyOutputs()
    target_sizes = torch.tensor([[100, 100]])
    text_queries = ["building"]

    with pytest.raises(ModelExecutionError) as exc_info:
        adapter._post_process_results(outputs, target_sizes, text_queries, threshold=0.1, orig_w=100, orig_h=100)

    assert exc_info.value.code == "GROUNDING_POSTPROCESS_UNSUPPORTED"
    assert "Installed OWL-ViT processor does not expose a supported post-processing API" in str(exc_info.value)


def test_grounding_bbox_normalization_and_validation():
    """Verify coordinate normalization ensures x1 < x2 and y1 < y2 and clamped to [0, 1]."""
    adapter = RsGroundingModel(model_id="google/owlvit-base-patch32")

    # Inverted box coordinates that require sorting
    mock_proc = MagicMock()
    mock_proc.post_process_grounded_object_detection.return_value = [
        {
            "boxes": torch.tensor([
                [80.0, 90.0, 20.0, 10.0],  # x1 > x2, y1 > y2
                [-10.0, -20.0, 150.0, 120.0],  # Out-of-bounds coords
            ]),
            "scores": torch.tensor([0.80, 0.65]),
            "labels": torch.tensor([0, 0]),
            "text_labels": ["structure", "field"],
        }
    ]

    adapter._processor = mock_proc
    outputs = DummyOutputs()
    target_sizes = torch.tensor([[100, 100]])
    text_queries = ["structure", "field"]

    regions = adapter._post_process_results(outputs, target_sizes, text_queries, threshold=0.5, orig_w=100, orig_h=100)

    assert len(regions) == 2
    # First box: inverted coords sorted and normalized
    b1 = regions[0]["bbox"]
    assert b1[0] <= b1[2]
    assert b1[1] <= b1[3]
    assert b1 == [0.2, 0.1, 0.8, 0.9]

    # Second box: out of bounds clamped to [0.0, 1.0]
    b2 = regions[1]["bbox"]
    assert b2[0] >= 0.0 and b2[1] >= 0.0
    assert b2[2] <= 1.0 and b2[3] <= 1.0
    assert b2 == [0.0, 0.0, 1.0, 1.0]


# =========================================================================
# 2. OBJECT STORAGE INTEGRITY & ERROR TYPING TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_local_object_store_exists(tmp_path):
    """Verify LocalObjectStore.exists() returns True when file exists, False otherwise."""
    store = LocalObjectStore(base_path=str(tmp_path))

    # Test missing key
    assert await store.exists("images/test_missing/original.tif") is False

    # Create dummy file
    test_key = "images/test_exist/original.tif"
    full_path = tmp_path / "images" / "test_exist" / "original.tif"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(b"dummy geotiff data")

    assert await store.exists(test_key) is True


@pytest.mark.asyncio
async def test_download_bytes_missing_raises_storage_object_not_found(tmp_path):
    """Verify download_bytes raises StorageObjectNotFoundError with code IMAGE_OBJECT_MISSING."""
    store = LocalObjectStore(base_path=str(tmp_path))
    missing_key = "images/00000000-0000-0000-0000-000000000000/original.tif"

    with pytest.raises(StorageObjectNotFoundError) as exc_info:
        await store.download_bytes(missing_key)

    err = exc_info.value
    assert err.code == "IMAGE_OBJECT_MISSING"
    assert err.object_key == missing_key
    assert err.storage_status == "MISSING"


@pytest.mark.asyncio
async def test_image_service_storage_status():
    """Verify ImageService.get_storage_status accurately reports AVAILABLE vs MISSING."""
    db_mock = AsyncMock()
    img_id = uuid.uuid4()

    # Image with missing storage
    img_missing = MagicMock(spec=ImageModel)
    img_missing.id = img_id
    img_missing.original_filename = "missing.tif"
    img_missing.object_key = f"images/{img_id}/original.tif"
    img_missing.preview_key = f"images/{img_id}/preview.png"

    db_res = MagicMock()
    db_res.scalar_one_or_none.return_value = img_missing
    db_mock.execute.return_value = db_res

    mock_store = AsyncMock()
    mock_store.exists.return_value = False

    with patch("app.services.image_service.get_object_store", return_value=mock_store):
        res = await ImageService.get_storage_status(img_id, db_mock)
        assert res["status"] == "MISSING"
        assert res["original_exists"] is False

    # Image with available storage
    mock_store.exists.side_effect = lambda k: "original" in k
    with patch("app.services.image_service.get_object_store", return_value=mock_store):
        res = await ImageService.get_storage_status(img_id, db_mock)
        assert res["status"] == "AVAILABLE"
        assert res["original_exists"] is True


# =========================================================================
# 3. PAIR VALIDATION CONSISTENCY TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_temporal_pair_rejects_missing_storage():
    """Verify TemporalPairService marks pair as INVALID_STORAGE when T1 or T2 is missing from storage."""
    service = TemporalPairService()
    pair_id = uuid.uuid4()
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()

    pair_mock = MagicMock(spec=BiTemporalPairModel)
    pair_mock.id = pair_id
    pair_mock.image_t1_id = t1_id
    pair_mock.image_t2_id = t2_id
    pair_mock.acquisition_time_t1 = None
    pair_mock.acquisition_time_t2 = None
    pair_mock.spatially_compatible = True
    pair_mock.temporally_valid = True
    pair_mock.overlap_ratio = 0.95
    pair_mock.alignment_status = "NOT_REQUIRED"
    pair_mock.registration_method = "IDENTITY"
    pair_mock.registration_metadata = {}
    pair_mock.validation_result_json = None
    pair_mock.created_at = "2026-09-01T00:00:00"

    t1_mock = MagicMock(spec=ImageModel)
    t1_mock.id = t1_id
    t1_mock.original_filename = "t1.tif"
    t1_mock.acquisition_time = None
    t1_mock.crs = "EPSG:32643"
    t1_mock.width = 100
    t1_mock.height = 100
    t1_mock.resolution_x = 10.0
    t1_mock.resolution_y = 10.0
    t1_mock.object_key = f"images/{t1_id}/original.tif"
    t1_mock.preview_key = f"images/{t1_id}/preview.png"

    t2_mock = MagicMock(spec=ImageModel)
    t2_mock.id = t2_id
    t2_mock.original_filename = "t2.tif"
    t2_mock.acquisition_time = None
    t2_mock.crs = "EPSG:32643"
    t2_mock.width = 100
    t2_mock.height = 100
    t2_mock.resolution_x = 10.0
    t2_mock.resolution_y = 10.0
    t2_mock.object_key = f"images/{t2_id}/original.tif"
    t2_mock.preview_key = f"images/{t2_id}/preview.png"

    session_mock = AsyncMock()
    session_mock.get.side_effect = [pair_mock, t1_mock, t2_mock]

    # Simulate t1 exists but t2 missing from storage
    async def fake_exists(key):
        return str(t1_id) in key

    mock_store = AsyncMock()
    mock_store.exists.side_effect = fake_exists

    with patch("app.temporal.service.get_object_store", return_value=mock_store):
        result = await service.get_pair(pair_id, session_mock)

        assert result is not None
        assert result.validation.valid is False
        assert result.validation.status_code == "INVALID_STORAGE"


@pytest.mark.asyncio
async def test_cross_modal_pair_rejects_missing_storage():
    """Verify CrossModalPairService marks pair as INVALID_STORAGE when Optical or SAR is missing from storage."""
    service = CrossModalPairService()
    pair_id = uuid.uuid4()
    opt_id = uuid.uuid4()
    sar_id = uuid.uuid4()

    cm_mock = MagicMock(spec=OpticalSARPairModel)
    cm_mock.id = pair_id
    cm_mock.optical_image_id = opt_id
    cm_mock.sar_image_id = sar_id
    cm_mock.optical_sensor = "Cartosat-2"
    cm_mock.sar_sensor = "RISAT-1"
    cm_mock.spatial_compatibility = "COMPATIBLE"
    cm_mock.registration_status = "ALIGNED"
    cm_mock.validation_status = "VALID"
    cm_mock.overlap_ratio = 0.90
    cm_mock.alignment_method = "IDENTITY"
    cm_mock.alignment_metadata = {}
    cm_mock.validation_result_json = None
    cm_mock.optical_modality = "OPTICAL"
    cm_mock.sar_modality = "SAR"
    cm_mock.created_at = "2026-09-01T00:00:00"
    cm_mock.updated_at = "2026-09-01T00:00:00"

    opt_mock = MagicMock(spec=ImageModel)
    opt_mock.id = opt_id
    opt_mock.original_filename = "opt.tif"
    opt_mock.modality = "OPTICAL"
    opt_mock.sensor = "Cartosat-2"
    opt_mock.crs = "EPSG:32643"
    opt_mock.resolution_x = 10.0
    opt_mock.bounds = {"left": 0, "bottom": 0, "right": 100, "top": 100}
    opt_mock.acquisition_time = None
    opt_mock.band_count = 3
    opt_mock.dtype = "uint8"
    opt_mock.object_key = f"images/{opt_id}/original.tif"
    opt_mock.preview_key = f"images/{opt_id}/preview.png"

    sar_mock = MagicMock(spec=ImageModel)
    sar_mock.id = sar_id
    sar_mock.original_filename = "sar.tif"
    sar_mock.modality = "SAR"
    sar_mock.sensor = "RISAT-1"
    sar_mock.crs = "EPSG:32643"
    sar_mock.resolution_x = 10.0
    sar_mock.bounds = {"left": 0, "bottom": 0, "right": 100, "top": 100}
    sar_mock.acquisition_time = None
    sar_mock.band_count = 1
    sar_mock.dtype = "float32"
    sar_mock.polarization = "VV"
    sar_mock.object_key = f"images/{sar_id}/original.tif"
    sar_mock.preview_key = f"images/{sar_id}/preview.png"

    session_mock = AsyncMock()
    session_mock.get.side_effect = [cm_mock, opt_mock, sar_mock]

    # Simulate both missing from storage
    mock_store = AsyncMock()
    mock_store.exists.return_value = False

    with patch("app.cross_modal.service.get_object_store", return_value=mock_store):
        result = await service.get_pair(pair_id, session_mock)

        assert result is not None
        assert result.validation.valid is False
        assert result.validation.status_code == "INVALID_STORAGE"
        assert "missing from object storage" in result.validation.message
