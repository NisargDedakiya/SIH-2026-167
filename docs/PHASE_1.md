# SatQuery AI — Phase 1 Scope & Boundary Report

**Problem Statement ID:** 26167  
**Organization:** Indian Space Research Organisation (ISRO)  
**Phase 1 Title:** Foundation & Geospatial Ingestion Layer

---

## 1. Scope & Implemented Deliverables

Phase 1 establishes the operational substrate required for all downstream remote-sensing and multimodal AI tasks:

1. **Geospatial Ingestion Engine**:
   - File format inspection (`GeoTIFF`, `TIFF`, `PNG`, `JPEG`).
   - Magic byte header inspection preventing extension spoofing.
   - Configurable upload limits (`MAX_UPLOAD_SIZE_MB`).
   - Safe windowed reading via Rasterio / GDAL to avoid RAM bloat.
2. **Metadata Extraction**:
   - Technical raster specs: width, height, band count, data type.
   - Geospatial referencing: CRS string, EPSG code, Affine transform matrix, bounding box (west/south/east/north), resolution / GSD.
   - Clear distinction: `is_geospatial = true` when valid geotransform and CRS exist, `false` otherwise.
3. **Contrast Normalization & Visual Preview**:
   - Percentile contrast stretching (2%–98%) for 16-bit satellite bands.
   - Multi-band RGB selection strategy.
   - Downsampling capped at 2048x2048 to produce fast browser-friendly previews.
4. **Data Persistence**:
   - PostgreSQL / PostGIS database schema with UUID primary keys.
   - S3 / MinIO compatible storage backend with local filesystem fallback.
   - Extensible JSON auxiliary metadata table.
5. **Security & Validation Architecture**:
   - Path traversal immunity using randomized storage keys: `images/{uuid}/original.{ext}`.
   - Sanitized original filenames for display.
   - Tri-state validation reporting: `valid`, `warning`, `error`.
   - Comprehensive error handling masking raw internal server traces from end-users.
6. **Web Dashboard**:
   - Next.js 14+ / React / Tailwind dark-themed GIS dashboard.
   - Drag-and-drop file upload with progress feedback.
   - Zoom/pan inspection canvas with real-time metadata cards.
   - Future AI Query Box with explicit disabled state: *"AI analysis will be available in Phase 2."*
7. **Future AI Architecture Contracts**:
   - `AnalysisAgent` abstract interface.
   - `SpecialistModel` base contract.
   - `ToolRegistry` placeholder definitions for single VQA, captioning, grounding, change detection, and optical-SAR analysis.

---

## 2. Intentionally Excluded from Phase 1

To preserve modular integrity and avoid fragile toy implementations, the following features are reserved for subsequent phases:
- **Phase 2**: Remote Sensing Vision-Language Models (RS-VLM) and single-image VQA.
- **Phase 3**: Multi-turn agentic orchestration, tool-use execution, and thought traces.
- **Phase 4**: Visual grounding, bounding-box detection, and pixel-level segmentation masks.
- **Phase 5**: Bi-temporal change detection and change VQA.
- **Phase 6**: Optical + SAR co-registered pair fusion.
- **Phases 7–10**: Remote-sensing domain adaptation, benchmark evaluation, report generation, and full SIH deployment.
