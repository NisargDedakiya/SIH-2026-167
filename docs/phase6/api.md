# Phase 6: REST API Specification

## 1. Pair Management Endpoints

### `POST /api/v1/cross-modal/pairs`
Registers an Optical-SAR pair.
- **Request Body**:
  ```json
  {
    "optical_image_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "sar_image_id": "8fa85f64-5717-4562-b3fc-2c963f66afb7"
  }
  ```
- **Response (201 Created)**: `OpticalSARPairResponse`

### `GET /api/v1/cross-modal/pairs`
Lists registered Optical-SAR pairs with pagination.
- **Query Params**: `limit` (default 50), `offset` (default 0).

### `GET /api/v1/cross-modal/pairs/{pair_id}`
Retrieves details, alignment status, and overlap metrics for a pair.

### `POST /api/v1/cross-modal/pairs/{pair_id}/validate`
Re-runs spatial compatibility and modality checking.

---

## 2. Analysis Endpoints

### `POST /api/v1/cross-modal/analyze`
Executes joint multimodal analysis.
- **Request Body**:
  ```json
  {
    "pair_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "query": "Analyze both sensors for water bodies and flood inundation.",
    "task": "cross_modal_analysis"
  }
  ```
- **Response (200 OK)**: `CrossModalAnalysisResponse`

### `POST /api/v1/analysis/cross-modal`
Direct agent endpoint for cross-modal queries.

### `POST /api/v1/analysis/cross-modal-vqa`
Direct agent endpoint for cross-modal VQA.

### `POST /api/v1/analysis/cross-modal-grounding`
Direct agent endpoint for cross-modal spatial bounding box grounding.

### `GET /api/v1/analysis/{analysis_id}/cross-modal-evidence`
Retrieves localized bounding box regions and attribution metadata.
