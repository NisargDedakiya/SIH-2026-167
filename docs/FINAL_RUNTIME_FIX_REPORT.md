# SatQuery AI — Final Runtime Debugging & Integration Fix Report

**Problem Statement**: ISRO SIH Problem 26167 — Agentic Multimodal AI for Satellite Imagery Analysis  
**Repository Version**: Current Active Codebase  
**Date**: September 26, 2026  
**Status**: RESOLVED & VALIDATED (164/164 tests passing, Next.js production build clean)

---

## 1. Executive Summary & Diagnostic Findings

The recent testing screenshots identified two distinct runtime failures affecting the demonstration workflows:

1. **Failure A (Screenshots B & C — Demo 3 & Demo 4)**:
   - **Failing Request**: `GET /api/v1/images?limit=100` returning `HTTP 500`.
   - **Impact**: Blocked image discovery for Demo 3 (Bi-temporal Change Detection) and Demo 4 (Cross-Modal Optical-SAR Fusion).

2. **Failure B (Screenshot A — Demo 2)**:
   - **Failing Request**: `POST /api/v1/agent/analyze` returning `HTTP 500`.
   - **Impact**: Visual grounding query (*"Highlight the buildings in this image."*) failed with an uninformative 500 error instead of a typed response indicating model availability or execution state.

3. **Auxiliary Issue (Offline Pill Display)**:
   - The status badge displayed `🔴 Offline` despite the backend being reachable, caused by a misunderstanding between lightweight `/health` liveness and deep `/ready` dependency state.

---

## 2. Exact Root Cause Analysis

### Failure A: `GET /api/v1/images?limit=100` (HTTP 500)
- **Root Cause**:
  1. **Schema Drift on Existing Volumes**: The application had evolved `ImageModel` to include 26 columns (`acquisition_time`, `sensor`, `modality`, `is_geospatial`, `validation_status`, `preview_key`, `pair_id`, `cross_modal_pair_id`, etc.), but relied solely on `Base.metadata.create_all(engine)`. In SQLAlchemy, `create_all` only creates *missing tables*; it **never** alters existing tables to add newly defined columns.
  2. In persistent Docker volumes (or existing local databases created during earlier iterations), querying `select(ImageModel)` forced PostgreSQL/SQLite to execute `SELECT images.acquisition_time, images.sensor, ... FROM images`. This resulted in `UndefinedColumn: column images.acquisition_time does not exist`.
  3. The unhandled database exception was intercepted by FastAPI's generic exception handler and converted to an opaque `HTTP 500`.
  4. Additionally, a duplicate `@classmethod` decorator on `ImageService.get_inspect_response` turned the method into an uncallable descriptor in Python when invoked via `cls.get_inspect_response(...)`.

### Failure B: `POST /api/v1/agent/analyze` (HTTP 500 on Demo 2)
- **Root Cause**:
  1. **Exception Swallowing in `ToolExecutor`**: `SingleImageGroundingTool` routes to `remote-sensing-grounding` (`google/owlvit-base-patch32`). When the model was not preloaded or when network restrictions blocked downloading 600MB+ weights at runtime, `ModelUnavailableError` was raised.
  2. `AnalysisService` intended to return `HTTP 503 MODEL_UNAVAILABLE`. However, `ToolExecutor.execute_plan()` wrapped all tool execution calls in a blanket `except Exception as e:` block and re-raised them as `PlanExecutionError(f"Step failed: {e}")`.
  3. The global FastAPI exception handler treated `PlanExecutionError` as an unexpected 500 internal server error. This hid the root cause and deprived the UI and user of actionable information (`MODEL_UNAVAILABLE`).
  4. At the model layer, `OwlViTProcessor.from_pretrained` and `OwlViTForObjectDetection.from_pretrained` did not prioritize local offline cache files (`local_files_only=True`), attempting unnecessary network HEAD requests that hung or failed in disconnected demo environments.

---

## 3. Database Migration & Session Architecture Fixes

### Alembic Migration Pipeline
We established a proper, production-grade schema migration framework:
- Configured [backend/alembic.ini](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic.ini) and [alembic.ini](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/alembic.ini).
- Created [backend/alembic/env.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/env.py) reading database configuration dynamically from `settings.DATABASE_URL` with async engine support.
- Generated initial baseline version: [backend/alembic/versions/001_initial_schema.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/versions/001_initial_schema.py).
- Created non-destructive column verification upgrade: [backend/alembic/versions/002_verify_and_upgrade_columns.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/versions/002_verify_and_upgrade_columns.py), ensuring all 26 `ImageModel` columns and job pair columns exist without dropping any historical data.

### Self-Healing Runtime Migration in `backend/app/database/session.py`
To guarantee the application boots cleanly on existing databases without requiring manual shell intervention:
1. `init_db()` now performs an automatic schema introspection pass across PostgreSQL (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) and SQLite (`PRAGMA table_info`).
2. Performs a schema smoke query on startup:
   ```sql
   SELECT id, original_filename, acquisition_time, sensor, modality, is_geospatial, validation_status FROM images LIMIT 1
   ```
3. Exposes `check_db_schema_ready() -> tuple[bool, str]`, ensuring `/ready` reports `DATABASE_SCHEMA_MISMATCH` if any schema divergence is detected.

### Image Service Hardening (`backend/app/services/image_service.py`)
- Removed the duplicate `@classmethod` decorator on `get_inspect_response`.
- Handled `ImageMetadataModel` as strictly optional: if an extensible metadata record is absent, empty warnings `[]` are safely supplied.
- Robust parsing for bounding boxes, spatial resolution, and affine transforms.
- Added explicit schema mismatch error handling in `list_images()` returning `HTTP 503 DATABASE_SCHEMA_MISMATCH` with structured error details instead of generic 500.

---

## 4. Typed Error Propagation & Model Handling Fixes

### Tool Executor (`backend/app/agent/executor.py`)
Refactored `ToolExecutor.execute_plan()` to preserve typed exceptions:
- **`HTTPException`**: Re-raised directly without modification.
- **`ModelUnavailableError`**: Re-raised as `HTTPException(status_code=503, detail={"code": "MODEL_UNAVAILABLE", "message": str(e), ...})`.
- **`UnsupportedModalityError`**: Re-raised as `HTTPException(status_code=400, detail={"code": "UNSUPPORTED_MODALITY", ...})`.
- **`InferenceError`**: Re-raised as `HTTPException(status_code=500, detail={"code": "MODEL_EXECUTION_FAILURE", ...})`.
- **`PlanExecutionError`**: Re-raised as `HTTPException(status_code=500, detail={"code": "TOOL_EXECUTION_FAILURE", ...})`.

### FastAPI Global Exception Handler (`backend/app/main.py`)
Updated `http_exception_handler` to unpack structured dictionaries passed in `exc.detail`. The error envelope returned to clients now consistently conforms to:
```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "Specialist grounding model google/owlvit-base-patch32 is unavailable.",
    "details": {},
    "trace_id": "8a7c2e11-..."
  }
}
```

### Offline-First Model Adapters & Cache Preparation
1. **Offline Loading**: Updated `RsGroundingModel`, `RsVqaModel`, and `RsCaptionModel` to attempt loading with `local_files_only=True` first, immediately utilizing cached checkpoints in `.cache/huggingface/hub` without hitting external network timeouts.
2. **Model Preparation Script**: Created [scripts/prepare_models.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/scripts/prepare_models.py), allowing operators to verify and pre-cache:
   - `google/owlvit-base-patch32` (Visual Grounding)
   - `Salesforce/blip-vqa-base` (VQA Foundation)
   - `satquery-rs-v1` (Domain-Adapted Remote Sensing LoRA Adapter)
   - `Salesforce/blip-image-captioning-base` (Dense Captioning)

---

## 5. Health vs. Readiness Architecture Fixes

### Lightweight `/health` (Liveness)
- Kept strictly lightweight:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "database": "not_checked",
    "storage": "not_checked"
  }
  ```
- Does not assert database or storage connectivity falsely.

### Deep `/ready` (Readiness)
- Probes all core subsystems:
  - Database schema consistency via `check_db_schema_ready()`.
  - Object store access via `store.list_objects()`.
  - Model registry count (`len(models) > 0`).
  - GPU / CPU execution device availability.
- Returns `HTTP 503` with exact error codes if broken:
  - `DATABASE_SCHEMA_MISMATCH`
  - `MODEL_REGISTRY_UNAVAILABLE`
  - `STORAGE_UNAVAILABLE`

### Frontend Status State Machine
In [frontend/app/demo/page.tsx](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/frontend/app/demo/page.tsx) and navigation components:
- `health=200` + `ready=200` &rarr; `ONLINE` (Green)
- `health=200` + `ready=503` &rarr; `DEGRADED` (Yellow)
- `health!=200` &rarr; `OFFLINE` (Red)

---

## 6. Frontend Execution Diagnostic Report & Demo Pair Discovery

### Execution Diagnostic Report
Enhanced the error UI on the Demonstration Hub ([frontend/app/demo/page.tsx](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/frontend/app/demo/page.tsx)):
- Displays a structured 5-column diagnostic grid:
  - **STEP**: Failed execution phase (e.g., `Agent Execution`, `Image Discovery`)
  - **ENDPOINT**: HTTP API endpoint (e.g., `/api/v1/agent/analyze`)
  - **HTTP STATUS**: Exact status code (e.g., `503`, `500`)
  - **ERROR CODE**: Typed error code (e.g., `MODEL_UNAVAILABLE`, `DATABASE_SCHEMA_MISMATCH`)
  - **TRACE ID**: Full UUID trace link for root-cause tracking
- Provides contextual **Suggested Actions** (e.g., *"Run scripts/prepare_models.py to verify local Hugging Face checkpoints"*).

### Demo 3 & Demo 4 Resilient Pair Discovery
- **Demo 3 (Bi-temporal)**:
  1. Checks registered pairs via `/api/v1/temporal/pairs`.
  2. Fallback: Discovers two images from `/api/v1/images` with identical sensor/modality, valid acquisition timestamps, and spatial overlap.
  3. If none exist: Halts with `DEMO_INPUT_UNAVAILABLE` explaining missing temporal pairs rather than passing mismatched images.
- **Demo 4 (Cross-Modal Optical-SAR)**:
  1. Checks registered pairs via `/api/v1/cross-modal/pairs`.
  2. Fallback: Discovers one optical image (`optical`) and one SAR image (`sar`) with spatial overlap and compatible resolution.
  3. If none exist: Halts with `DEMO_INPUT_UNAVAILABLE` explaining missing cross-modal pairs.

---

## 7. Verification & Test Results

### 1. Dedicated Runtime Fixes Test Suite
Executed [backend/tests/test_runtime_fixes.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/tests/test_runtime_fixes.py):
- `test_list_images_existing_database`: **PASSED** (200 OK, full ImageInspectResponse contract validated)
- `test_model_registry_non_empty`: **PASSED** (all 6 specialist models verified)
- `test_grounding_typed_error_preservation`: **PASSED** (ModelUnavailableError &rarr; 503 MODEL_UNAVAILABLE)
- `test_agent_analyze_grounding_end_to_end`: **PASSED** (Grounding plan execution, trace sequence preserved)
- `test_health_and_readiness_probes`: **PASSED** (Liveness and readiness contract validated)

### 2. Full Backend Test Suite
Executed `python -m pytest backend/tests -q`:
```
........................................................................ [ 43%]
........................................................................ [ 87%]
....................                                                     [100%]
164 passed, 189 warnings in 23.67s
```
**Result: 164 passed out of 164 tests (100% pass rate).**

### 3. Frontend Production Build
Executed `npm run build` in `frontend/`:
```
   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (13/13)
   Finalizing page optimization ...
   Collecting build traces ...
```
**Result: All 13 routes compiled and typed cleanly without warnings or errors.**

---

## 8. Summary of Modified & Created Files

| File | Type | Changes |
| :--- | :--- | :--- |
| [backend/alembic.ini](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic.ini) | Created | Alembic configuration for migrations |
| [alembic.ini](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/alembic.ini) | Created | Root Alembic configuration |
| [backend/alembic/env.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/env.py) | Created | Async migration engine setup |
| [backend/alembic/versions/001_initial_schema.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/versions/001_initial_schema.py) | Created | Initial schema baseline |
| [backend/alembic/versions/002_verify_and_upgrade_columns.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/alembic/versions/002_verify_and_upgrade_columns.py) | Created | Non-destructive column additions |
| [backend/app/database/session.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/database/session.py) | Modified | Auto-migration on boot, smoke tests, schema readiness |
| [backend/app/services/image_service.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/services/image_service.py) | Modified | Removed duplicate `@classmethod`, optional metadata safety, 503 on schema error |
| [backend/app/agent/executor.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/agent/executor.py) | Modified | Preserved `HTTPException` and typed `ModelUnavailableError` (503) |
| [backend/app/services/analysis_service.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/services/analysis_service.py) | Modified | Structured error envelopes with `code`, `message`, `details` |
| [backend/app/main.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/main.py) | Modified | FastAPI exception handler unpacking dict details |
| [backend/app/ai/models/rs_grounding_adapter.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/ai/models/rs_grounding_adapter.py) | Modified | Offline-first `local_files_only=True` loading |
| [backend/app/api/health.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/api/health.py) | Modified | Lightweight `/health`, deep `/ready` schema & model check |
| [backend/app/schemas/common.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/schemas/common.py) | Modified | Added `DATABASE_SCHEMA_MISMATCH`, `MODEL_REGISTRY_UNAVAILABLE` |
| [scripts/prepare_models.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/scripts/prepare_models.py) | Created | Standalone offline model cache preparation utility |
| [frontend/app/demo/page.tsx](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/frontend/app/demo/page.tsx) | Modified | Diagnostic report with code/traceId, resilient pair discovery |
| [backend/tests/test_runtime_fixes.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/tests/test_runtime_fixes.py) | Created | Regression test suite for runtime fixes |
| [backend/tests/test_health.py](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/tests/test_health.py) | Modified | Updated test assertions for liveness probe |

---

## 9. Operational Guidance for Live Demonstration

1. **Development Reset vs. Production Upgrade**:
   - For a fresh start: `docker compose down -v && docker compose up --build`
   - For an existing persistent database: Booting the backend will automatically upgrade existing tables without losing previously uploaded imagery.
2. **Model Checkpoint Cache**:
   - Run `python scripts/prepare_models.py` once on the host before judging sessions to verify all models are cached locally.
   - Mounted model directory `/models/huggingface` in Docker allows zero-network inference during presentations.
3. **Status Distinction**:
   - If models are still being loaded or cached: system status displays `DEGRADED` (yellow), not `OFFLINE` (red).
   - If a specific model is missing: system gracefully raises `503 MODEL_UNAVAILABLE` with clear diagnostic logs and trace IDs, rather than an unexplained `500`.
