# Phase 4 — Grounding & Visual Evidence Engine

## Overview & SIH Alignment
Phase 4 implements the **Text-Guided Visual Grounding & Evidence Engine** for SatQuery AI, fulfilling the core Smart India Hackathon (SIH Problem 26167) mandate:
> *"Produce evidence-grounded textual and visual results for remote sensing imagery, enabling verification of AI answers via pixel-level localization and native geospatial coordinates."*

In Phase 3, SatQuery could interpret natural language queries and route them to specialist models. In Phase 4, SatQuery makes all findings **visually verifiable** by locating spatial features, rendering evidence overlays, cropping high-resolution regions, computing geospatial bounds in the native CRS, and recording auditable execution facts.

---

## System Architecture

```text
User Query: "Highlight the water body in this image."
                       │
                       ▼
            ┌─────────────────────┐
            │   SATQUERY AGENT    │
            │  CapabilityResolver │
            │   WorkflowPlanner   │
            └──────────┬──────────┘
                       │ Task: GROUNDING
                       │ Tool: single_image_grounding
                       ▼
            ┌─────────────────────┐
            │   GROUNDING TOOL    │
            │ (RsGroundingModel / │
            │ MockGroundingModel) │
            └──────────┬──────────┘
                       │ Raw Detections: [x1, y1, x2, y2]
                       ▼
      ┌───────────────────────────────────┐
      │     EVIDENCE SUBSYSTEM ENGINE     │
      │ 1. geometry.py                    │
      │    - Normalized -> Raster Pixels  │
      │    - Affine Transform -> CRS BBox │
      │ 2. overlay.py                     │
      │    - Render Overlay (Alpha Fill)  │
      │    - Render Region Crops (PNG)    │
      │ 3. artifacts.py                   │
      │    - Upload to Object Storage     │
      │ 4. renderer.py & SQLite           │
      │    - Persist to 'evidence' table  │
      └─────────────────┬─────────────────┘
                        │
                        ▼
      ┌───────────────────────────────────┐
      │      RESULT & AUDIT CONTRACT      │
      │ - Text Answer                     │
      │ - Evidence Geometry & CRS Bounds  │
      │ - Overlay & Crop Artifacts        │
      │ - Observable Facts Trace          │
      └───────────────────────────────────┘
```

---

## Model Selection & Research
A detailed comparative analysis was conducted and documented in [`docs/GROUNDING_MODEL_RESEARCH.md`](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/docs/GROUNDING_MODEL_RESEARCH.md):
- **OWLv2 (`google/owlvit-base-patch32` / `google/owlv2-base-patch16-ensemble`)**: Selected as the baseline open-vocabulary zero-shot grounding specialist. Supports arbitrary natural language queries without closed-vocabulary retraining.
- **Grounding DINO**: High precision on complex natural features, evaluated for large-scale multi-GPU deployments.
- **VRSBench / RSVQAx**: Benchmarks used for remote-sensing prompt normalization and spatial prior tuning.
- **Inference Runtime Adapter**: Implemented in [`app/ai/models/grounding/rs_grounding_adapter.py`](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/ai/models/grounding/rs_grounding_adapter.py) with dual-mode CPU/GPU execution and deterministic fallback via `MockGroundingModel`.

---

## Coordinate Systems & Geometry Mapping

SatQuery enforces explicit, unambiguous coordinate semantics across three distinct spaces:

| Coordinate Space | Domain | Representation | Example |
| :--- | :--- | :--- | :--- |
| **Model Coordinates** | $[0.0, 1.0]$ | `[x1, y1, x2, y2]` normalized | `[0.25, 0.50, 0.75, 0.85]` |
| **Raster Pixel Space** | $[0, W] \times [0, H]$ | `{"x1", "y1", "x2", "y2", "width", "height"}` | `{1000, 1500, 3000, 2550, 2000, 1050}` |
| **Native Geospatial CRS** | Real-world units (meters / degrees) | `{"crs", "bounds": {min_x, min_y, max_x, max_y}, "polygon"}` | `EPSG:32643 [500100.0, 2999500.0] to [500300.0, 2999800.0]` |

### Coordinate Invariants
1. Normalized bounding boxes are clamped within $[0.0, 1.0]$.
2. Pixel geometries are clamped within the raster's actual $W \times H$ dimensions.
3. Reprojection into native CRS uses `rasterio.transform.xy(aff, row, col, offset='ul')` ensuring corners strictly align with raster pixel cells.
4. Non-georeferenced images gracefully omit `geo_geometry` (`None`) without crashing.

---

## Database Schema (`evidence` table)

Created [`EvidenceModel`](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/app/database/models.py) in SQLite:
```sql
CREATE TABLE evidence (
    id VARCHAR(36) PRIMARY KEY,
    analysis_id VARCHAR(36) NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    image_id VARCHAR(36) NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    type VARCHAR(32) NOT NULL,            -- e.g. 'bounding_box', 'segmentation_mask'
    label VARCHAR(128) NOT NULL,          -- e.g. 'water body', 'building cluster'
    confidence FLOAT NOT NULL,            -- e.g. 0.91
    geometry_json JSON NOT NULL,          -- Normalized [x1, y1, x2, y2]
    pixel_geometry_json JSON NOT NULL,    -- Pixel coordinates {x1, y1, x2, y2, width, height}
    geo_geometry_json JSON,               -- Native CRS polygon and bounds
    artifact_key VARCHAR(512),            -- Object store key to overlay PNG
    crop_artifact_key VARCHAR(512),       -- Object store key to region crop PNG
    created_at TIMESTAMP NOT NULL
);
```

---

## API Endpoints

1. `POST /api/v1/analysis/grounding`: Direct text-guided grounding analysis on an image.
2. `GET /api/v1/analysis/{analysis_id}/evidence`: Enumerate all persistent visual evidence records for an analysis job.
3. `GET /api/v1/analysis/evidence/{evidence_id}`: Retrieve a specific visual evidence record.
4. `GET /api/v1/analysis/evidence/{evidence_id}/artifact?crop=false`: Fetch the PNG overlay image.
5. `GET /api/v1/analysis/evidence/{evidence_id}/artifact?crop=true`: Fetch the high-resolution region crop PNG.

---

## Frontend Components

1. **`EvidenceViewer` (`frontend/components/evidence-viewer.tsx`)**:
   - 3 view modes: **Interactive Vector SVG**, **Rendered Overlay**, and **Original Raster**.
   - Zoom and Pan controls ($50\%$ to $300\%$, Fullscreen mode).
   - Interactive bounding box selection with dynamic pulse highlights and HUD pills.
   - Region list sidebar displaying confidence scores, pixel geometry, and native CRS coordinates.
   - High-resolution region crop preview with direct download/tab inspection.
2. **`QueryPanel` Integration (`frontend/components/query-panel.tsx`)**:
   - Automatically embeds `EvidenceViewer` when the SatQuery agent resolves a grounding task.
   - Direct Grounding tab with dedicated quick query chips (*"Highlight the water body"*, *"Where are the buildings?"*, *"Highlight the road network"*).

---

## Acceptance Verification Results

All 5 required Phase 4 acceptance scenarios were verified through automated tests in [`backend/tests/test_grounding.py`](file:///c:/Users/nisar/OneDrive/Desktop/SIH2026-167/backend/tests/test_grounding.py):

| Test Case | Query | Resolved Tool | Evidence Output | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1** | *"Highlight the water body."* | `single_image_grounding` | 1 region (`water body`), confidence $91\%$, overlay & crop generated | **PASSED** |
| **Case 2** | *"Where are the buildings?"* | `single_image_grounding` | 2 regions (`commercial structure`, `residential building`), overlay generated | **PASSED** |
| **Case 3** | *"Describe this scene."* | `single_image_caption` | Caption generated, **0 visual evidence records** (no hallucinated boxes) | **PASSED** |
| **Case 4** | *"What type of land cover is visible?"* | `single_image_vqa` | VQA answer generated, **0 visual evidence records** | **PASSED** |
| **Case 5** | *"What changed between these images?"* | `None` (Planned) | Controlled non-fallback, **0 grounding invoked** | **PASSED** |

### Test Suite Execution
- `pytest tests/test_grounding.py tests/test_agent.py`: **28 passed in 4.20s**
- Full test suite `pytest`: **55 passed in 7.44s**
- Frontend typecheck & bundle: `npx tsc --noEmit` (**0 errors**) & `npm run build` (**100% clean production build**)
