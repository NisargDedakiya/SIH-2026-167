# SatQuery AI — System Architecture

**Problem Statement ID:** 26167  
**Title:** SatQuery AI - An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries  
**Organization:** Indian Space Research Organisation (ISRO)

---

## 1. High-Level Vision & Phase Progression

SatQuery AI is designed to progress from a rock-solid geospatial ingestion foundation into a fully agentic multimodal vision-language system.

```
┌─────────────────────────────────────────────────────────────┐
│                    SATQUERY AI ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────┘
                            │
               ┌────────────▼────────────┐
               │    Web Client (Next.js) │
               └────────────┬────────────┘
                            │ REST / WebSocket
               ┌────────────▼────────────┐
               │   FastAPI Core Engine   │
               └──────┬───────────┬──────┘
                      │           │
          ┌───────────▼┐         ┌▼──────────────┐
          │ Validation │         │  Geospatial   │
          │  Pipeline  │         │ Raster Engine │
          └───────────┬┘         └┬──────────────┘
                      │           │
               ┌──────▼───────────▼──────┐
               │  Image Ingestion Core   │
               └──────┬───────────┬──────┘
                      │           │
          ┌───────────▼┐         ┌▼──────────────┐
          │ PostgreSQL │         │ MinIO/S3      │
          │  + PostGIS │         │ Object Store  │
          └────────────┘         └───────────────┘
                      │
        ─────────────────────────────── Future Phases
                      │
               ┌──────▼───────────┐
               │  Analysis Agent  │ (Phase 3)
               └──────┬───────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 ┌───────────┐  ┌───────────┐  ┌───────────┐
 │ RS-VLM    │  │ Grounding │  │ Change    │
 │ Specialist│  │ Specialist│  │ Specialist│ (Phases 2, 4-6)
 └───────────┘  └───────────┘  └───────────┘
```

---

## 2. Phase 1 Pipeline Architecture

Phase 1 provides the core ingestion vertical slice:

1. **Client Upload**:
   - Multipart chunked upload via Next.js dashboard.
   - Client-side size & format pre-flight checks.
2. **Ingestion & Security Gate (`backend/app/geospatial/validator.py`)**:
   - File extension verification (`.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`).
   - Magic byte header inspection (TIFF `II*\x00` / `MM\x00*`, PNG `\x89PNG`, JPEG `\xff\xd8\xff`).
   - Size limit validation (configurable via `MAX_UPLOAD_SIZE_MB`).
   - UUID generation (`images/{uuid}/original.{ext}`).
3. **Raster Engine (`backend/app/geospatial/`)**:
   - **Safe Reading (`reader.py`)**: Windowed reads, GDAL overviews check, memory caps to prevent Out-Of-Memory (OOM) crashes on large gigabyte rasters.
   - **Metadata Extraction (`metadata.py`)**: Raster dimensions, band count, data type, nodata value, coordinate reference systems (CRS/EPSG), affine geotransform, geospatial bounding box coordinates.
   - **Contrast Normalization (`normalization.py`)**: Percentile-based stretching (2%–98%) tailored for high-dynamic-range (12-bit/16-bit) satellite imagery.
   - **Preview Generation (`preview.py`)**: High-fidelity RGB downsampled previews (capped at 2048x2048 max dim) saved as web-friendly PNGs.
4. **Storage Layer (`backend/app/storage/`)**:
   - S3/MinIO compatible object store for raster binaries and generated previews.
   - Local disk storage fallback for isolated development/test environments.
5. **Database Layer (`backend/app/database/`)**:
   - PostgreSQL + PostGIS stores normalized image records and extensible JSON metadata.
6. **Frontend Experience (`frontend/`)**:
   - Space-tech dark theme inspired by satellite operations centers.
   - Drag-and-drop uploader with real-time feedback.
   - Interactive zoom/pan visualizer.
   - Granular raster and geospatial metadata cards with accessible validation badges.

---

## 3. Future AI Contracts (Interfaces Established in Phase 1)

To ensure later phases plug in seamlessly without rewriting Phase 1:
- `core/contracts/agent.py`: `AnalysisAgent` contract defining `analyze(query, image_ids, context)`.
- `core/contracts/specialist.py`: `SpecialistModel` defining inputs, preprocessing, predictions, evidence extraction, and confidence metrics.
- `core/contracts/tools.py`: `ToolRegistry` defining tool capabilities (`single_vqa`, `caption`, `grounding`, `change_detection`, `change_vqa`, `optical_sar_analysis`).
