# SatQuery AI — UI, API & Runtime Integration Error Audit

**Audit Date:** 2026-09-26  
**System:** SatQuery AI (Multimodal Remote Sensing Intelligence Platform)  
**Investigation Scope:** Frontend App, Next.js Proxy, FastAPI Backend, Model Registry, Geospatial Ingestion & Object Storage

---

## 1. Executive Summary

A comprehensive end-to-end repository audit identified six interconnected root causes spanning the communication and schema layers between the browser, Next.js standalone server, FastAPI backend, and AI model runtime. 

The core architecture and analytical algorithms are sound; however, proxy routing omissions, unhandled abstract methods in model adapters, schema property misalignments, and broad Git ignore rules prevented normal operation in Docker and web interfaces.

---

## 2. Discovered Root Causes & Detailed Findings

### Issue 1: Header Incorrectly Displays "Offline"
- **Observed Symptom:** Top-right navigation banner persistently shows `🔴 Offline`.
- **Root Cause:**
  1. `frontend/components/app-shell.tsx` executes `fetch("/health")`.
  2. `frontend/next.config.js` only defined a proxy rewrite for `/api/v1/:path*`. No rewrites existed for `/health` or `/ready`.
  3. Next.js handled `GET /health` internally as an unmatched client-side route (returning 404 HTML), causing `AppShell` to mark `isHealthy = false`.
  4. Additionally, `AppShell` lacked multi-state status distinction (`CONNECTING`, `ONLINE`, `DEGRADED`, `OFFLINE`).

### Issue 2: Next.js Docker Backend Proxy Misconfiguration
- **Observed Symptom:** Frontend requests inside Docker fail to reach backend services.
- **Root Cause:**
  1. In `docker-compose.yml`, `docker-compose.dev.yml`, and `docker-compose.demo.yml`, `frontend.environment.NEXT_PUBLIC_API_URL` was set to `http://localhost:8000`.
  2. Inside a Docker container, `localhost:8000` refers to the container's own network namespace, where nothing listens on port 8000.
  3. Next.js server-side rewrites need an internal backend URL (`SATQUERY_BACKEND_URL: http://backend:8000` in Docker), with fallback to `http://localhost:8000` for host development.

### Issue 3: Empty AI Model Registry (`Available tasks: []`)
- **Observed Symptom:** VQA and analytical queries report:
  `No AI model available for task visual_question_answering. Available tasks: []`.
- **Root Cause:**
  1. `backend/app/ai/models/grounding/rs_grounding_adapter.py` (`RsGroundingModel`) inherits from `SpecialistModel` (an abstract base class in `app/ai/base.py`) but failed to implement three required abstract methods: `postprocess()`, `confidence()`, and `evidence()`.
  2. When `ModelRuntime.initialize_models()` ran during application startup, instantiating `RsGroundingModel` threw:
     `TypeError: Can't instantiate abstract class RsGroundingModel without an implementation for abstract methods 'confidence', 'evidence', 'postprocess'`.
  3. `backend/app/main.py` lifespan caught the exception as a deferred warning. Because `runtime` was assigned before `initialize_models()` failed, subsequent calls retrieved a singleton with an empty `_task_map` (`{}`).
  4. Deep readiness probe (`/ready`) in `backend/app/api/health.py` marked readiness as `ready (empty)` rather than failing with HTTP 503 when models were uninitialized.

### Issue 4: "Failed to fetch" in Demo Hub (Demos 1–4)
- **Observed Symptom:** All four demonstration scenarios fail with generic `Failed to fetch`.
- **Root Cause:**
  1. `frontend/lib/api.ts` used `const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"`, making direct absolute requests rather than same-origin `/api/v1/...` requests proxied by Next.js.
  2. `frontend/app/demo/page.tsx` blindly took `imagesList.slice(0, neededCount)` without verifying modality (Optical vs SAR), pair compatibility, or existence.
  3. Network failures were caught and surfaced merely as `"Failed to fetch"`, without diagnostics on execution step, endpoint, HTTP status, or remedy.

### Issue 5: Blank Previews in Image Catalog
- **Observed Symptom:** Raster cards display black empty rectangles for `t1.tif`, `t2.tif`, and `malicious.tif`.
- **Root Cause:**
  1. `getImagePreviewUrl` was imported by multiple components from `@/lib/api`, but was completely missing from `frontend/lib/api.ts`.
  2. `frontend/app/images/page.tsx` implemented an `onError` handler that set `style.display = "none"`, suppressing failed requests and preventing error diagnostics.
  3. `backend/app/services/image_service.py` returned HTTP 500 when storage objects were missing instead of a clean `PREVIEW_NOT_FOUND` (HTTP 404).

### Issue 6: Metadata Schema Mismatch (`Dimensions: x`, `Bands: ch`, `CRS: Unprojected`, `GSD: N/A`)
- **Observed Symptom:** Image catalog displays placeholder text instead of raster dimensions and geospatial parameters.
- **Root Cause:**
  1. The backend contract (`ImageInspectResponse`) returns structured nested objects:
     `raster: { width, height, bands, dtype, nodata }`
     `geospatial: { is_geospatial, crs, epsg, resolution: { x, y } }`
  2. `frontend/app/images/page.tsx` accessed flat legacy properties: `img.width`, `img.height`, `img.channels`, `img.crs`, `img.gsd_meters`, all of which were undefined.

### Issue 7: Input Inspector CRS & Resolution Inconsistency
- **Observed Symptom:** Input Inspector showed "Pixel Frame" even when EPSG:32643 was recognized.
- **Root Cause:**
  1. `frontend/components/input-inspector.tsx` accessed `image.geospatial?.resolution_x` instead of `image.geospatial?.resolution?.x`.
  2. CRS resolution bypassed EPSG if `image.geospatial?.crs` was null/empty, falling back to "Pixel Frame" instead of formatting `EPSG:${epsg}`.
  3. A hardcoded fake fallback (`"10.0 m (nom.)"`) was used when resolution was missing.

### Issue 8: Broad `.gitignore` Excluding `frontend/lib/`
- **Observed Symptom:** GitHub repository ZIP omitted `frontend/lib/`.
- **Root Cause:**
  1. Root `.gitignore` line 23 contained `lib/` (intended for Python virtual environment builds), which matched `frontend/lib/` anywhere in the tree.
  2. `frontend/lib/api.ts`, `frontend/lib/types.ts`, and `frontend/lib/presentation-utils.ts` were ignored by Git.

### Issue 9: PEFT / LoRA Training Module Import Path
- **Observed Symptom:** Fragile imports between root `training/` and `backend/training/`.
- **Root Cause:**
  1. `backend/app/ai/models/vqa/rs_adapted_vqa.py` imports `from training.peft_adapter import LoRAManager`.
  2. When executed from repository root without setting `PYTHONPATH=backend`, Python resolved `training/` to root (which contained `train_rs_adapter.py` but not `peft_adapter.py`).

---

## 3. Corrective Action Plan

| Priority | Component | Correction |
|---|---|---|
| 🔴 Critical | `.gitignore` | Replace broad `lib/` with `/lib/` and `/lib64/` to untrack only root virtualenvs; ensure `frontend/lib` is tracked |
| 🔴 Critical | `frontend/next.config.js` | Add `/health`, `/ready`, and `/api/v1/:path*` rewrites using `SATQUERY_BACKEND_URL` |
| 🔴 Critical | `docker-compose*.yml` | Provide `SATQUERY_BACKEND_URL: http://backend:8000` to frontend service |
| 🔴 Critical | `frontend/lib/api.ts` | Restore canonical same-origin API client with `requestApi()` wrapper, X-Request-ID, and `getImagePreviewUrl` |
| 🔴 Critical | `backend/app/ai/models/` | Implement missing abstract methods in `RsGroundingModel` and harmonize `CrossModalFusionModel` |
| 🔴 Critical | `backend/app/ai/runtime.py` & `/ready` | Ensure complete model registration and fail `/ready` with 503 if model registry is empty |
| 🔴 Critical | `frontend/app/demo/page.tsx` | Implement validated input selection for Demos 1–4 and detailed diagnostics instead of "Failed to fetch" |
| 🟠 High | `frontend/app/images/page.tsx` | Use canonical schema (`img.raster.*`, `img.geospatial.*`); implement Preview loading/error/retry UI |
| 🟠 High | `frontend/components/input-inspector.tsx` | Fix CRS (`EPSG:{epsg}`) and GSD resolution (`resolution.x`); eliminate fake fallbacks |
| 🟠 High | `frontend/components/app-shell.tsx` | Implement multi-state health check (`CONNECTING`, `ONLINE`, `DEGRADED`, `OFFLINE`) |
