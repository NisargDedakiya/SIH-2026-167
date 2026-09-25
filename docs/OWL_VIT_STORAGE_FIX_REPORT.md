# SatQuery AI — OWL-ViT & Object Storage Consistency Fix Report
**ISRO Smart India Hackathon (Problem ID: 26167)**  
**Date:** 2026-09-26  
**System Status:** 🟢 Online & Healthy  

---

## 1. Executive Summary

This report documents the resolution of the two remaining runtime failures affecting SatQuery AI:
1. **Demo 2 (Grounding):** `MODEL_EXECUTION_FAILURE: OwlViTProcessor object has no attribute 'post_process_object_detection'`
2. **Demo 3 & Demo 4 (Temporal & Optical-SAR Analysis):** `INTERNAL_ERROR: Storage key not found: images/.../original.tif`

Both issues have been resolved at the architectural level without downgrading global dependencies, without using mock models or synthetic predictions, and without destructive database modifications.

---

## 2. Technical Investigation & Root Causes

### 2.1 Failure 1: OWL-ViT Processor API Evolution
- **Installed Transformers Version:** `transformers==5.17.0`
- **Root Cause:** In modern Hugging Face Transformers (v5.x / late v4.x), `OwlViTProcessor` deprecated and removed the legacy `post_process_object_detection` method in favor of `post_process_grounded_object_detection`, which accepts text queries and returns grounded candidate entities. The legacy call caused an immediate `AttributeError`.
- **Constraint Respected:** Downgrading `transformers` globally was strictly avoided because SatQuery AI relies on this version for the BLIP Visual Question Answering backbone, captioning LoRA adapters, and multi-modal embeddings.

### 2.2 Failure 2 & 3: Database ↔ Object Storage Drift
- **Root Cause:** PostgreSQL / SQLite database records had survived container recreation or storage volume wipes, whereas the physical GeoTIFF raster files in `./backend/data/storage/` (or MinIO `images/<uuid>/original.tif`) had been deleted.
- **Mechanism:** When an analysis was requested for a historical database record, the agent called the analysis tool, which attempted to open the non-existent key, resulting in `FileNotFoundError` / `NoSuchKey`, which previously bubbled up as an uninformative `500 INTERNAL_ERROR`.

---

## 3. Implemented Solutions

### 3.1 OWL-ViT Compatibility Layer (`backend/app/ai/models/grounding/rs_grounding_adapter.py`)
A robust 4-stage post-processing cascade was implemented in `RsGroundingModel._post_process_results()`:

```python
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
```

#### Output Normalization & Bounds Clamping:
- Bounding boxes are guaranteed to satisfy $x_1 \le x_2$ and $y_1 \le y_2$ via coordinate sorting.
- Model pixel coordinates are clamped to $[0, \text{orig\_w}]$ and $[0, \text{orig\_h}]$, then normalized to $[0.0, 1.0]$.
- Standardized output structure:
  ```json
  {
    "task": "grounding",
    "result": {
      "regions": [
        {
          "bbox": [0.12, 0.34, 0.56, 0.78],
          "label": "building",
          "confidence": 0.82,
          "pixel_geometry": { "x1": 12, "y1": 34, "x2": 56, "y2": 78, "width": 44, "height": 44 }
        }
      ]
    }
  }
  ```

---

### 3.2 Storage Integrity Layer & Typed Error System

1. **Storage Abstraction Extension (`backend/app/storage/object_store.py`):**
   - Verified and hardened `exists(key: str) -> bool` on both `LocalObjectStore` and `MinIOObjectStore` (using `stat()` or S3 head-object without full downloads).
   - In `download_bytes()`, missing keys now raise `StorageObjectNotFoundError`.

2. **Typed Exception (`backend/app/storage/exceptions.py`):**
   ```python
   class StorageObjectNotFoundError(StorageError):
       def __init__(self, key: str, message: Optional[str] = None, image_id: Optional[str] = None):
           self.code = "IMAGE_OBJECT_MISSING"
           self.object_key = key
           self.image_id = image_id
           self.storage_status = "MISSING"
   ```

3. **HTTP 409 Conflict Mapping (`backend/app/main.py` & `executor.py`):**
   - When a raster is registered in the database catalog but missing in object storage, the system rejects the operation with **HTTP 409 Conflict** and semantic code `IMAGE_OBJECT_MISSING` (instead of HTTP 500).

4. **Pair Pre-flight Storage Validation:**
   - `TemporalPairService.get_pair()` and `list_pairs()` verify `await storage.exists(img_t1.object_key)` and `await storage.exists(img_t2.object_key)`.
   - `CrossModalPairService.get_pair()` and `list_pairs()` verify optical and SAR raster existence.
   - Pairs with missing rasters are flagged with `valid=False, status_code="INVALID_STORAGE"`.

5. **Demo Hub Frontend Selection & UI (`frontend/app/demo/page.tsx`):**
   - Demos 1 & 2 dynamically prioritize verified optical/grounding rasters.
   - Demos 3 & 4 filter for pairs where `status_code !== "INVALID_STORAGE" && valid !== false`.
   - When an `IMAGE_OBJECT_MISSING` error occurs, the UI displays a dedicated **INPUT DATA ERROR** diagnostic panel showing the Image ID, Storage Key, Storage: MISSING, and Action: "Re-upload the image."

---

## 4. Storage Audit & Seeding

### 4.1 Storage Audit Tool (`backend/scripts/verify_storage_integrity.py`)
Executed audit against the database and storage:
```
==================================================
SATQUERY STORAGE INTEGRITY
==================================================
Database images:        324
Original objects:
  Available:            11
  Missing:              313
Preview objects:
  Available:            11
  Missing:              313
Broken image records:   313
Orphaned storage files: 22
==================================================
```

### 4.2 Demo Assets Seeding (`backend/scripts/seed_demo_assets.py`)
Official GeoTIFFs from `./demo/` were ingested with complete physical raster storage and metadata registration:
- **Grounding Raster:** `demo_grounding.tif` (`c20b2ee5-116d-4041-91f3-f7cd2c314bd0`)
- **Bi-Temporal T1:** `demo_t1.tif` (`7e74ffd2-21e6-4d10-b37e-cf8b67c5bc94`)
- **Bi-Temporal T2:** `demo_t2.tif` (`bfb345c7-89aa-47af-b191-5cf6452b6384`)
- **Bi-Temporal Pair:** `5cb4b9ed-f55a-4b0d-a08b-20d572630bfa` (Status: VALID, Overlap: 1.0)
- **Optical Raster:** `demo_optical.tif` (`0a43f001-9c2f-459c-8f32-872a531223d7`)
- **SAR Raster:** `demo_sar.tif` (`c517e5cc-4f81-4580-ac32-e98c83261983`)
- **Optical-SAR Pair:** `7a39dd15-30b6-414c-b3e7-b9bd020906df` (Status: VALID, Overlap: 1.0)

---

## 5. Verification & Test Results

### 5.1 Unit & Regression Suite (`backend/tests/test_owlvit_storage_fixes.py`)
All 10 unit and regression tests pass cleanly:
```
tests/test_owlvit_storage_fixes.py::test_owlvit_postprocess_grounded_object_detection PASSED
tests/test_owlvit_storage_fixes.py::test_owlvit_postprocess_legacy_object_detection PASSED
tests/test_owlvit_storage_fixes.py::test_owlvit_postprocess_image_processor_fallback PASSED
tests/test_owlvit_storage_fixes.py::test_owlvit_postprocess_unsupported_raises_typed_error PASSED
tests/test_owlvit_storage_fixes.py::test_grounding_bbox_normalization_and_validation PASSED
tests/test_owlvit_storage_fixes.py::test_local_object_store_exists PASSED
tests/test_owlvit_storage_fixes.py::test_download_bytes_missing_raises_storage_object_not_found PASSED
tests/test_owlvit_storage_fixes.py::test_image_service_storage_status PASSED
tests/test_owlvit_storage_fixes.py::test_temporal_pair_rejects_missing_storage PASSED
tests/test_owlvit_storage_fixes.py::test_cross_modal_pair_rejects_missing_storage PASSED

======================== 10 passed in 0.15s ========================
```

### 5.2 Live End-to-End Demonstration Execution (`scratch/test_demos_live.py`)
Tested through live Next.js reverse proxy (`http://localhost:3000`) hitting live FastAPI backend (`http://localhost:8000`):

| Scenario | Task Code | Target Image/Pair | HTTP Status | Evidence / Outcome |
| :--- | :--- | :--- | :---: | :--- |
| **Demo 1** | `VISUAL_QUESTION_ANSWERING` | `demo_grounding.tif` | **200 OK** | Land cover classified; Confidence: 0.88 |
| **Demo 2** | `GROUNDING` | `demo_grounding.tif` | **200 OK** | OWL-ViT grounded detector executed without crash |
| **Demo 3** | `CHANGE_ANALYSIS` | Pair `5cb4b9ed...` | **200 OK** | 15 changed regions, 71.9% scene area mapped |
| **Demo 4** | `CROSS_MODAL_ANALYSIS` | Pair `7a39dd15...` | **200 OK** | Optical-SAR joint reasoning & fusion executed |
| **Broken Raster Test** | Direct Tool Access | ID `0639d84b...` | **409 Conflict** | Error: `IMAGE_OBJECT_MISSING` (Clean Input Data Error) |

---

## 6. Files Changed

| Component | File Path | Description |
| :--- | :--- | :--- |
| **AI Specialist** | `backend/app/ai/models/grounding/rs_grounding_adapter.py` | Multi-tier OWL-ViT compatibility layer and bounding box normalizer. |
| **AI Errors** | `backend/app/ai/exceptions.py` | Added `ModelExecutionError` with `code`, `message`, and `details`. |
| **Storage Error** | `backend/app/storage/exceptions.py` | Created `StorageObjectNotFoundError` with code `IMAGE_OBJECT_MISSING`. |
| **Common Schemas**| `backend/app/schemas/common.py` | Added `IMAGE_OBJECT_MISSING` and `GROUNDING_POSTPROCESS_UNSUPPORTED` enum values. |
| **Storage Core** | `backend/app/storage/object_store.py` | Verified `exists()`; made `download_bytes()` raise `StorageObjectNotFoundError`. |
| **Image Service** | `backend/app/services/image_service.py` | Implemented `get_storage_status()`; updated `validate_image()`. |
| **Image API** | `backend/app/api/images.py` | Exposed `GET /api/v1/images/{id}/storage-status`. |
| **Analysis** | `backend/app/services/analysis_service.py` | Pre-flight check on `store.exists()`; returns 409 `IMAGE_OBJECT_MISSING`. |
| **Temporal** | `backend/app/temporal/service.py` | Validates raster storage on T1/T2; marks broken pairs `INVALID_STORAGE`. |
| **Cross-Modal** | `backend/app/cross_modal/service.py` | Validates raster storage on Optical/SAR; marks broken pairs `INVALID_STORAGE`. |
| **Agent Executor**| `backend/app/agent/executor.py` | Intercepts missing storage and model execution errors, emitting typed 409/500s. |
| **Global Handler**| `backend/app/main.py` | Standardized HTTP 409 translation to `IMAGE_OBJECT_MISSING` error schema. |
| **Demo Frontend** | `frontend/app/demo/page.tsx` | Valid pair filtering; specialized `INPUT DATA ERROR` card layout. |
| **Integrity Tool**| `backend/scripts/verify_storage_integrity.py` | Non-destructive database ↔ storage consistency audit CLI. |
| **Seeding Tool** | `backend/scripts/seed_demo_assets.py` | Ingests official demo rasters and registers valid multi-modal pairs. |
| **Test Suite** | `backend/tests/test_owlvit_storage_fixes.py` | 10 unit/integration tests for processor compatibility and storage integrity. |

---

## 7. Operational Guidelines for SIH Evaluation

### 7.1 Development Reset Procedure vs. Production Data Hygiene
- **Never rely on `docker compose down -v` in production:** Wiping volumes deletes the backing MinIO / local storage while leaving orphaned database state if external Postgres is used.
- **Repair Utility:** Run `python -m scripts.verify_storage_integrity` prior to presentations to audit all assets.
- **Missing Object Recovery:** If a database image displays `Storage: MISSING`, re-upload the GeoTIFF via the Ingest Hub rather than deleting database records.

---

## 8. Definition of Done Checklist

- [x] OWL-ViT processor API compatibility implemented and tested.
- [x] Grounding post-processing works on installed `transformers==5.17.0`.
- [x] Grounding boxes are normalized ($x_1 \le x_2, y_1 \le y_2 \in [0, 1]$).
- [x] Grounding coordinate mapping to geospatial CRS preserved.
- [x] No fake grounding output or fabricated predictions.
- [x] `object_store.exists()` implemented and tested.
- [x] Image storage status API endpoint (`/storage-status`) implemented.
- [x] Storage integrity audit script (`verify_storage_integrity.py`) implemented.
- [x] Typed error `StorageObjectNotFoundError` with code `IMAGE_OBJECT_MISSING` implemented.
- [x] Demo 3 validates storage before running analysis.
- [x] Demo 4 validates storage before running analysis.
- [x] Temporal pairs reject missing objects with `INVALID_STORAGE`.
- [x] Optical/SAR pairs reject missing objects with `INVALID_STORAGE`.
- [x] Missing objects produce dedicated `INPUT DATA ERROR` on frontend.
- [x] No generic storage 500 internal errors.
- [x] Fresh upload produces both original object and preview PNG.
- [x] VQA remains operational with BLIP backbone.
- [x] System health remains `Online 🟢` across `/health` and `/ready`.
- [x] All 10 regression tests pass.
- [x] End-to-end live testing of Demos 1, 2, 3, and 4 verified.
