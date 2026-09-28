# SatQuery AI — Practical Troubleshooting Manual

**Project:** SatQuery AI  
**Scope:** Real Runtime Issues, Root Cause Diagnoses, Verified Solutions, and Diagnostic Commands  

---

## 1. Issue Matrix

| Error Code / Symptom | Component | Root Cause | Verified Solution |
| :--- | :--- | :--- | :--- |
| `ImportError: DLL load failed while importing _base` | Geospatial Engine (`rasterio`) | Windows Application Control (AppLocker/WDAC) blocks binary `.pyd` on Windows host | Run backend inside Docker container or WSL2. |
| `DATABASE_SCHEMA_MISMATCH` / `UndefinedColumn` | Database (`ImageModel`) | Existing volume predates 26-column schema; `create_all` does not alter existing tables | Run `alembic upgrade head` or rely on self-healing `init_db()`. |
| `IMAGE_OBJECT_MISSING` / `409 Conflict` | Storage (`ObjectStore`) | Database record survived while physical raster in MinIO/local storage was deleted | Run `verify_storage_integrity.py` or re-upload raster. |
| `AttributeError: OwlViTProcessor` | Grounding Model | Transformers v4.38+/v5.x deprecated `post_process_object_detection` | Use 4-stage fallback cascade in `RsGroundingModel`. |
| `MODEL_UNAVAILABLE` / `503 Service Unavailable` | Specialist Runtime | Checkpoint weights missing or model download blocked by offline network | Run `python scripts/prepare_models.py` to pre-cache models. |
| `ALIGNMENT_FAILURE` / `400 Bad Request` | Temporal / Cross-Modal | Two satellite images have $< 10\%$ spatial intersection or non-overlapping CRS bounds | Verify geographic coordinates of both rasters. |
| Status Badge Shows `🔴 Offline` | Frontend App Shell | Frontend was checking deep `/ready` probe instead of lightweight `/health` | Resolved in Phase 10: badge checks `/health` for liveness. |

---

## 2. In-Depth Root Cause & Resolutions

### 2.1 Rasterio DLL Blocked on Windows Host (`_base.pyd`)
- **Symptom:**
  ```text
  ImportError while loading conftest:
  from rasterio._base import DatasetBase
  ImportError: DLL load failed while importing _base: An Application Control policy has blocked this file.
  ```
- **Cause:** Modern Windows Enterprise/Education environments enforce Windows Defender Application Control (WDAC) or AppLocker policies that prevent unsigned or user-directory C-extension binaries (`.pyd` DLLs) from executing under Python 3.13 in `AppData\Local`.
- **Solution:**
  1. **Primary (Recommended):** Run the backend in Docker:
     ```bash
     docker compose up --build backend
     ```
     The Linux container (`python:3.11-slim`) compiles and runs `rasterio` and GDAL natively without host OS restrictions.
  2. **Secondary:** Execute within Windows Subsystem for Linux (WSL2 Ubuntu).

---

### 2.2 Database ↔ Storage Drift (`IMAGE_OBJECT_MISSING`)
- **Symptom:**
  ```json
  {
    "error": {
      "code": "IMAGE_OBJECT_MISSING",
      "message": "Storage key not found: images/8f6a7c8b.../original.tif",
      "details": {"storage_status": "MISSING", "suggested_action": "Re-upload the source raster"}
    }
  }
  ```
- **Cause:** Persistent database volumes retained historical `images` rows, but the backing MinIO volume or `./data/storage/` folder was wiped or recreated during container maintenance.
- **Solution:**
  1. Run the storage integrity verification utility:
     ```bash
     python backend/scripts/verify_storage_integrity.py
     ```
  2. Delete orphaned records or re-upload the target satellite imagery via `/images/upload`.
  3. Pre-seed demo assets:
     ```bash
     python backend/scripts/seed_demo_assets.py
     ```

---

### 2.3 OWL-ViT Processor API Evolution
- **Symptom:**
  ```text
  AttributeError: 'OwlViTProcessor' object has no attribute 'post_process_object_detection'
  ```
- **Cause:** Hugging Face `transformers` evolved its API. Modern versions use `post_process_grounded_object_detection` with text query labels.
- **Solution:** `RsGroundingModel._post_process_results()` implements an automated 4-stage introspection cascade:
  1. Checks for `processor.post_process_grounded_object_detection`
  2. Falls back to `processor.post_process_object_detection`
  3. Falls back to `processor.image_processor.post_process_object_detection`
  4. Explicitly raises `GROUNDING_POSTPROCESS_UNSUPPORTED` if none match.

---

### 2.4 Database Schema Divergence (`alembic` & `init_db`)
- **Symptom:**
  ```text
  UndefinedColumn: column images.acquisition_time does not exist
  ```
- **Cause:** SQLAlchemy's `create_all()` never alters existing tables to add newly defined columns.
- **Solution:**
  Run the automated migration script:
  ```bash
  cd backend
  alembic upgrade head
  ```
  `backend/app/database/session.py` also runs non-destructive `ALTER TABLE images ADD COLUMN IF NOT EXISTS` self-healing queries during startup.

---

### 2.5 CUDA Out-Of-Memory (OOM) or GPU Unavailable
- **Symptom:**
  ```text
  torch.cuda.OutOfMemoryError: CUDA out of memory.
  ```
- **Cause:** High-resolution satellite rasters exceed available GPU VRAM.
- **Solution:**
  Set `AI_DEVICE=cpu` in `.env` to enforce safe CPU fallback:
  ```env
  AI_DEVICE=cpu
  ```
  `ModelRuntime` catches CUDA allocation failures and retries on CPU without crashing the FastAPI worker.
