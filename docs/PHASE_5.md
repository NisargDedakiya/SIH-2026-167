# Phase 5 — Bi-Temporal Change Intelligence

## Overview & SIH Alignment
Phase 5 implements the **Bi-Temporal Change Intelligence Subsystem** for SatQuery AI, directly fulfilling the core Smart India Hackathon (SIH Problem 26167) mandate for multi-temporal remote-sensing intelligence:
> *"Given two images of the same area at different times ($T_1$ and $T_2$), determine what changed, where it changed, describe the change, answer natural-language questions about it (Change VQA), extract discrete change regions with pixel and native CRS coordinates, render change overlay/map visual evidence, provide observable audit traces, and support interactive multi-mode temporal inspection."*

---

## Core System Architecture

```text
User Query: "What changed between these two dates?" / "Did urban development increase?"
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   SATQUERY AGENT CONTROLLER │
                        │  - Pair Resolution ($T_1, T_2$)   │
                        │  - Temporal Intent Detection │
                        │  - CapabilityResolver     │
                        └─────────────┬─────────────┘
                                      │ Task: CHANGE_ANALYSIS
                                      ▼
                        ┌───────────────────────────┐
                        │   TEMPORAL SUBSYSTEM      │
                        │ 1. validator.py           │
                        │    - $T_1 < T_2$ Temporal │
                        │    - CRS & Area Overlap   │
                        │ 2. alignment.py           │
                        │    - Bilinear Reproject   │
                        │    - Zero In-Place Edits  │
                        │ 3. change_detection model │
                        │    - Siamese Difference   │
                        │ 4. change_map.py          │
                        │    - Magnitude & Binary   │
                        │ 5. regions.py             │
                        │    - Pixel & CRS BBoxes   │
                        │ 6. description.py         │
                        │    - Structured Text Gen  │
                        │ 7. change_vqa.py          │
                        │    - Category Intelligence│
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   OUTPUT & AUDIT TRACE    │
                        │ - Change Description      │
                        │ - Answer + Confidence     │
                        │ - Change Metrics & Pct    │
                        │ - Region Bounding Boxes   │
                        │ - Dual-Canvas UI Overlays │
                        │ - Observable Facts Trace  │
                        └───────────────────────────┘
```

---

## Technical Invariants Preserved

1. **Non-Destructive Co-Registration**:
   - Original ingested satellite rasters are strictly read-only and never modified on disk or in object storage.
   - When rasters require alignment (differing dimensions, pixel spacing, or coordinate transforms), $T_2$ is non-destructively reprojected to $T_1$'s grid using `rasterio.warp.reproject` in-memory or persisted as a derived artifact (`pair_artifacts/`).
2. **Multi-Image Change Routing Invariant**:
   - When a user query includes multiple images or references a registered bi-temporal pair with change keywords, the classifier and resolver strictly route to `CHANGE_ANALYSIS`. It never falls back silently to single-image VQA or Captioning.
3. **Dual Coordinate Representation**:
   - Every extracted change region provides both pixel coordinates `[x_min, y_min, x_max, y_max]` (relative to $T_1$ raster grid) and native CRS geo-bounds `[min_x, min_y, max_x, max_y]` mapped through the affine transform.
4. **Observable Audit Traces**:
   - Every execution trace emits solely deterministic, observable engineering facts (e.g., pixel overlap ratio, change percentage, threshold, aligned dimensions, tool name, model name), with zero unobservable internal chain-of-thought tokens.
5. **Zero Regressions**:
   - Single-image VQA, Captioning, and Visual Grounding (Phases 1–4) remain 100% operational alongside Phase 5.

---

## Data Model & Database Schema

The SQLite/PostgreSQL schema is extended with:
- **`bi_temporal_pairs` Table (`BiTemporalPairModel`)**:
  - `id`: UUID primary key
  - `t1_image_id`: UUID foreign key referencing `images.id`
  - `t2_image_id`: UUID foreign key referencing `images.id`
  - `t1_timestamp` & `t2_timestamp`: ISO 8601 acquisition dates ($T_1 < T_2$)
  - `overlap_ratio`: Float (0.0 to 1.0)
  - `common_crs`: String (EPSG/Proj4)
  - `aligned`: Boolean flag
  - `alignment_method`: String ("bilinear_warp" / "native_grid")
  - `validation_json`: Stored JSON validation report
  - `registration_metadata`: Stored JSON affine transforms and resolutions
- **`analysis_jobs` Table Migration**:
  - Automatically migrated via `init_db()` with `pair_id` (UUID foreign key referencing `bi_temporal_pairs.id`).

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/temporal/pairs` | Register a new bi-temporal image pair ($T_1, T_2$) with validation |
| `GET` | `/api/v1/temporal/pairs` | List registered bi-temporal pairs with thumbnail summaries |
| `GET` | `/api/v1/temporal/pairs/{pair_id}` | Retrieve pair details, alignment state, and overlap metrics |
| `POST` | `/api/v1/temporal/pairs/{pair_id}/validate` | Trigger explicit geospatial overlap and temporal order validation |
| `POST` | `/api/v1/temporal/analyze` | Run full change analysis pipeline with custom sensitivity threshold |
| `POST` | `/api/v1/agent/analyze` | Unified agent endpoint accepting `pair_id` and natural language queries |
| `POST` | `/api/v1/analysis/change` | Direct REST endpoint for bi-temporal change analysis |
| `GET` | `/api/v1/analysis/pair/{pair_id}/jobs` | History of analysis jobs executed on a bi-temporal pair |

---

## Frontend Interactive Capabilities

The Bi-Temporal Analysis workspace (`/temporal`) delivers a modern, rich interface:
1. **Side-by-Side Synchronized View**:
   - Synchronous pan and zoom comparison of $T_1$ and $T_2$ acquisitions.
2. **Interactive Split Swipe Slider**:
   - Draggable vertical divider revealing $T_1$ on the left and $T_2$ on the right.
3. **Change Heatmap Overlay**:
   - Alpha-blended semi-transparent red change mask rendered directly over the base satellite raster.
4. **Discrete Change Regions Inspector**:
   - Visual bounding box vector overlays with click-to-inspect drawer showing pixel coordinates, native CRS bounds, area, and change intensity.
5. **Agentic Change VQA Chat**:
   - Pre-configured quick query chips for urban growth, vegetation shifts, building construction, and custom natural language prompts.
6. **Sensitivity Control**:
   - Real-time change threshold tuning slider (0.05 to 0.50) to filter environmental noise.
