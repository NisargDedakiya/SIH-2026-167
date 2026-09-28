# SatQuery AI — Complete REST API Reference

**Base Path:** `/api/v1`  
**API Specification:** OpenAPI 3.1.0 (`/openapi.json`)  
**Interactive Docs:** Swagger UI (`/docs`), ReDoc (`/redoc`)  
**Standard Response Format:** Structured JSON (`application/json`)  
**Standard Error Contract:**
```json
{
  "detail": "Descriptive message",
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation",
    "details": {},
    "trace_id": "4b68e91f-0e82-411f-829d-64906f362142"
  }
}
```

---

## 1. System Health & Probes

### Lightweight Liveness Probe
- **Method:** `GET`
- **Path:** `/health`
- **Description:** Fast liveness check indicating that the FastAPI process is receiving HTTP traffic. Does not probe external dependencies.
- **Response `200 OK`:**
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "database": "not_checked",
    "storage": "not_checked"
  }
  ```

### Deep Readiness Probe
- **Method:** `GET`
- **Path:** `/ready`
- **Description:** Deep dependency probe verifying database connectivity, schema synchronization, object store accessibility, registered specialist AI models, and hardware accelerator state.
- **Response `200 OK` (All Services Ready):**
  ```json
  {
    "status": "ready",
    "version": "0.1.0",
    "environment": "development",
    "services": {
      "database": "ready",
      "storage": "ready",
      "models": "ready (6 registered)",
      "gpu": "cuda_available (NVIDIA GeForce RTX ...)"
    }
  }
  ```
- **Response `503 Service Unavailable`:** Returned when any critical dependency is offline.

---

## 2. Remote-Sensing Imagery Endpoints (`/api/v1/images`)

### Upload & Ingest Satellite Raster
- **Method:** `POST`
- **Path:** `/api/v1/images/upload`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: Raster file (`.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`).
- **Validation:** Verifies magic bytes, checks max upload size (`500MB`), extracts native CRS, affine geotransform, and radiometric statistics, generates normalized PNG preview.
- **Response `201 Created`:**
  ```json
  {
    "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "filename": "sentinel2_sample.tif",
    "status": "valid",
    "message": "Image uploaded and processed successfully",
    "is_geospatial": true,
    "crs": "EPSG:32643",
    "bounds": {
      "left": 72.100,
      "bottom": 21.100,
      "right": 72.200,
      "top": 21.200
    }
  }
  ```

### List Uploaded Images
- **Method:** `GET`
- **Path:** `/api/v1/images?limit=50`
- **Query Parameters:**
  - `limit` (int, default 50): Max number of image records to retrieve.
- **Response `200 OK`:** Array of `ImageInspectResponse` objects.

### Inspect Image Metadata
- **Method:** `GET`
- **Path:** `/api/v1/images/{image_id}`
- **Path Parameters:**
  - `image_id` (UUID): Target image identifier.
- **Response `200 OK`:**
  ```json
  {
    "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "filename": "sentinel2_sample.tif",
    "format": "GeoTIFF",
    "size_bytes": 14285714,
    "raster": {
      "width": 2048,
      "height": 2048,
      "bands": 4,
      "dtype": "uint16"
    },
    "geospatial": {
      "is_geospatial": true,
      "crs": "EPSG:32643",
      "epsg": 32643,
      "bounds": {
        "left": 72.100,
        "bottom": 21.100,
        "right": 72.200,
        "top": 21.200
      },
      "resolution": {
        "x": 10.0,
        "y": 10.0
      },
      "transform": [10.0, 0.0, 72.100, 0.0, -10.0, 21.200]
    },
    "validation": {
      "valid": true,
      "warnings": [],
      "errors": []
    }
  }
  ```

### Revalidate Image
- **Method:** `POST`
- **Path:** `/api/v1/images/{image_id}/validate`
- **Response `200 OK`:** Image validation report.

### Check Object Storage Status
- **Method:** `GET`
- **Path:** `/api/v1/images/{image_id}/storage-status`
- **Response `200 OK`:**
  ```json
  {
    "image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "storage_backend": "minio",
    "original_key": "images/8f6a7c8b.../original.tif",
    "original_exists": true,
    "preview_key": "images/8f6a7c8b.../preview.png",
    "preview_exists": true
  }
  ```

### Download Browser Preview
- **Method:** `GET`
- **Path:** `/api/v1/images/{image_id}/preview`
- **Response `200 OK`:** Binary image stream (`image/png`) with HTTP caching headers (`Cache-Control: public, max-age=86400`).

### Delete Image Record & Storage
- **Method:** `DELETE`
- **Path:** `/api/v1/images/{image_id}`
- **Response `200 OK`:**
  ```json
  {
    "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "deleted": true,
    "message": "Image deleted successfully."
  }
  ```

---

## 3. Agentic Analysis Endpoints (`/api/v1/agent`)

### Execute Agentic Multimodal Analysis
- **Method:** `POST`
- **Path:** `/api/v1/agent/analyze`
- **Request Body (`AgentAnalyzeRequest`):**
  ```json
  {
    "query": "What type of land cover dominates this satellite image?",
    "image_ids": ["8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e"],
    "pair_id": null,
    "context": {
      "modality": "optical",
      "acquisition_year": 2024
    }
  }
  ```
- **Response `200 OK` (`AgentAnalyzeResponse`):**
  ```json
  {
    "agent_run_id": "9b12e345-f678-490a-bcde-1234567890ab",
    "query": "What type of land cover dominates this satellite image?",
    "normalized_query": "what type of land cover dominates this satellite image?",
    "intent": "VISUAL_QUESTION_ANSWERING",
    "task": "VISUAL_QUESTION_ANSWERING",
    "status": "completed",
    "answer": "The dominant land cover is dense mixed agricultural vegetation with scattered residential structures.",
    "observations": {
      "observed": ["Dense green spectral reflectance across 68% of the surface", "Rectilinear field parcel boundaries"],
      "inferred": ["Active crop cultivation during monsoon or post-monsoon season"],
      "uncertain": ["Specific crop typology cannot be verified at 10m spatial resolution"]
    },
    "confidence": {
      "score": 0.88,
      "category": "high",
      "basis": "Calibrated from VLM token probability (0.92) weighted by resolution suitability (0.84)."
    },
    "tool_used": "single_image_vqa",
    "trace": {
      "agent_run_id": "9b12e345-f678-490a-bcde-1234567890ab",
      "total_duration_ms": 342,
      "events": [
        {"milestone": "query_received", "timestamp_ms": 10},
        {"milestone": "intent_classified", "intent": "VISUAL_QUESTION_ANSWERING", "timestamp_ms": 25},
        {"milestone": "plan_generated", "tool": "single_image_vqa", "timestamp_ms": 32},
        {"milestone": "tool_executed", "duration_ms": 280, "timestamp_ms": 315},
        {"milestone": "aggregation_complete", "timestamp_ms": 342}
      ]
    },
    "evidence_ids": ["e7a8b9c0-1d2e-3f4a-5b6c-7d8e9f0a1b2c"]
  }
  ```

### List Registered Tools
- **Method:** `GET`
- **Path:** `/api/v1/agent/tools`
- **Response `200 OK`:** Array of tool descriptors with status (`available` or `planned`), supported modalities, and input requirements.

### Inspect Agent Run Details
- **Method:** `GET`
- **Path:** `/api/v1/agent/runs/{run_id}`
- **Response `200 OK`:** Detailed trace log, steps executed, raw parameters, and execution events.

---

## 4. Specialist Analysis Endpoints (`/api/v1/analysis`)

### Visual Question Answering (Direct)
- **Method:** `POST`
- **Path:** `/api/v1/analysis/vqa`
- **Request Body (`VqaRequest`):**
  ```json
  {
    "image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "query": "Is there a river visible in this image?",
    "model_name": "satquery-rs-v1"
  }
  ```
- **Response `200 OK`:** Direct VQA response with answer, confidence, and job metadata.

### Scene Captioning (Direct)
- **Method:** `POST`
- **Path:** `/api/v1/analysis/caption`
- **Request Body (`CaptionRequest`):**
  ```json
  {
    "image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "model_name": "remote-sensing-caption"
  }
  ```
- **Response `200 OK`:** Generated descriptive caption.

### Text-Guided Spatial Grounding (Direct)
- **Method:** `POST`
- **Path:** `/api/v1/analysis/grounding`
- **Request Body (`GroundingRequest`):**
  ```json
  {
    "image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "query": "Highlight the buildings",
    "confidence_threshold": 0.20
  }
  ```
- **Response `200 OK` (`GroundingResponse`):** Array of detected regions with pixel bounding boxes $[ymin, xmin, ymax, xmax]$, reprojected native coordinates, confidence scores, and evidence artifacts.

### Retrieve Analysis Evidence
- **Method:** `GET`
- **Path:** `/api/v1/analysis/{analysis_id}/evidence`
- **Response `200 OK`:** Array of evidence items associated with the analysis.

### Download Evidence Artifact
- **Method:** `GET`
- **Path:** `/api/v1/analysis/evidence/{evidence_id}/artifact`
- **Response `200 OK`:** Binary image crop stream (`image/png`).

### List Available Specialist Models
- **Method:** `GET`
- **Path:** `/api/v1/analysis/models`
- **Response `200 OK`:** Array of registered model specifications.

### Analysis History
- **Method:** `GET`
- **Path:** `/api/v1/analysis/history?limit=20`
- **Response `200 OK`:** Historical analysis jobs.

---

## 5. Bi-Temporal Analysis Endpoints (`/api/v1/temporal`)

### Register Bi-Temporal Image Pair
- **Method:** `POST`
- **Path:** `/api/v1/temporal/pairs`
- **Request Body (`BiTemporalPairCreateRequest`):**
  ```json
  {
    "t1_image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "t2_image_id": "9a0b1c2d-3e4f-5a6b-7c8d-9e0f1a2b3c4d",
    "label": "Urban Expansion 2020-2024"
  }
  ```
- **Response `201 Created`:** Registered pair with temporal verification ($T_1 < T_2$) and spatial overlap metrics.

### Validate Pair Compatibility
- **Method:** `POST`
- **Path:** `/api/v1/temporal/pairs/{pair_id}/validate`
- **Response `200 OK`:** Spatial intersection percentage, resolution compatibility, and CRS alignment status.

### Execute Temporal Change Analysis
- **Method:** `POST`
- **Path:** `/api/v1/temporal/analyze`
- **Request Body (`ChangeAnalysisRequest`):**
  ```json
  {
    "pair_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "query": "What changed between these two dates?"
  }
  ```
- **Response `200 OK`:** Quantitative change metrics (changed area %, change polygon count), visual difference map artifact, and natural-language narrative.

---

## 6. Optical + SAR Cross-Modal Endpoints (`/api/v1/cross-modal`)

### Register Optical-SAR Pair
- **Method:** `POST`
- **Path:** `/api/v1/cross-modal/pairs`
- **Request Body (`OpticalSARPairCreateRequest`):**
  ```json
  {
    "optical_image_id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
    "sar_image_id": "3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "label": "Cartosat Optical + RISAT SAR Fusion"
  }
  ```
- **Response `201 Created`:** Validated cross-modal pair record.

### Validate Cross-Modal Sensor Alignment
- **Method:** `POST`
- **Path:** `/api/v1/cross-modal/pairs/{pair_id}/validate`
- **Response `200 OK`:** Spatial intersection, coordinate alignment, and sensor modality confirmation.

### Execute Cross-Modal Analysis
- **Method:** `POST`
- **Path:** `/api/v1/cross-modal/analyze`
- **Request Body (`CrossModalAnalysisRequest`):**
  ```json
  {
    "pair_id": "5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
    "query": "Compare optical and SAR imagery."
  }
  ```
- **Response `200 OK`:** Dual-stream fusion findings, optical-specific insights, SAR structural backscatter, and explicit sensor disagreements.

---

## 7. Report Generation Endpoints (`/api/v1/reports`)

### Normalized Report Model
- **Method:** `GET`
- **Path:** `/api/v1/reports/{analysis_id}`
- **Response `200 OK`:** Unified report schema containing summary, metadata, observations, confidence, and evidence links.

### Machine-Readable JSON Export
- **Method:** `GET`
- **Path:** `/api/v1/reports/{analysis_id}/json`
- **Response `200 OK`:** Clean JSON format suitable for automated GIS ingest.

### Standalone Interactive HTML Export
- **Method:** `GET`
- **Path:** `/api/v1/reports/{analysis_id}/html`
- **Response `200 OK`:** Self-contained, responsive HTML file (`text/html`) with embedded styles, SVG charts, and evidence imagery.

### Publication-Grade Vector PDF Export
- **Method:** `GET`
- **Path:** `/api/v1/reports/{analysis_id}/pdf`
- **Response `200 OK`:** Formal two-column vector PDF (`application/pdf`) generated via ReportLab.

### Complete Deliverable ZIP Package
- **Method:** `GET`
- **Path:** `/api/v1/reports/{analysis_id}/package`
- **Response `200 OK`:** Sanitized ZIP archive (`application/zip`) containing:
  - `report.pdf`
  - `report.html`
  - `analysis.json`
  - `trace.json`
  - `evidence/` directory (all raw crops and masks)
  - `README.txt`

---

## 8. Benchmark Evaluation Endpoints (`/api/v1/evaluation`)

### Comprehensive Evaluation Matrix
- **Method:** `GET`
- **Path:** `/api/v1/evaluation/matrix`
- **Response `200 OK`:** System evaluation status across all registered datasets, models, agent queries, and calibration bins.

### Registered Benchmark Datasets
- **Method:** `GET`
- **Path:** `/api/v1/evaluation/datasets`
- **Response `200 OK`:** Available dataset adapters and local acquisition status.

### Benchmark Evaluation Tasks
- **Method:** `GET`
- **Path:** `/api/v1/evaluation/tasks`
- **Response `200 OK`:** Supported tasks (VQA, Captioning, Grounding, Change, Routing) and active metric suites.

### Calibration Reliability Data
- **Method:** `GET`
- **Path:** `/api/v1/evaluation/calibration`
- **Response `200 OK`:** Expected Calibration Error (ECE), Brier Score, and 5-bin reliability diagram metrics.

### Error Taxonomy Distribution
- **Method:** `GET`
- **Path:** `/api/v1/evaluation/errors`
- **Response `200 OK`:** Distribution of observed error modes across the 4-category taxonomy.
