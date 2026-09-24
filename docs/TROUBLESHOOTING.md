# SatQuery AI — Production Troubleshooting & Operations Manual

This guide documents diagnostic workflows, known failure modes, and recovery procedures for SatQuery AI.

---

## 1. Quick Diagnostics

Verify system readiness using the readiness probe:
```bash
curl -s http://localhost:8000/ready | jq
```
Expected output:
```json
{
  "status": "ready",
  "version": "0.1.0",
  "environment": "production",
  "services": {
    "database": "ready",
    "storage": "ready",
    "models": "ready (6 registered)",
    "gpu": "cpu_fallback"
  }
}
```

---

## 2. Common Failure Modes & Solutions

### 2.1 Backend Fails to Start
- **Symptom:** `uvicorn` terminates with database connection errors.
- **Cause:** PostgreSQL / PostGIS container is starting up or unreachable.
- **Solution:**
  - Verify container status: `docker compose ps`
  - For local development without Docker, use SQLite fallback:
    ```bash
    export DATABASE_URL=sqlite+aiosqlite:///./satquery.db
    ```

### 2.2 MinIO Storage Unavailable
- **Symptom:** Uploads fail with `Failed to upload raster to storage`.
- **Cause:** MinIO server on port 9000 is stopped or bucket has not initialized.
- **Solution:**
  - SatQuery AI features an automatic fallback to local disk storage (`STORAGE_BACKEND=local`).
  - Configure `LOCAL_STORAGE_PATH=./data/storage` in `.env`.

### 2.3 CUDA Unavailable / CPU Fallback
- **Symptom:** Models execute on CPU or log `ModelRuntime initialized using device: cpu`.
- **Cause:** PyTorch cannot find compatible NVIDIA drivers or CUDA toolkit.
- **Verification:** SatQuery AI automatically detects CUDA availability:
  ```python
  import torch
  print(torch.cuda.is_available())
  ```
- **Action:** No action required. SatQuery AI features automatic, seamless CPU fallback for all models and adapters.

### 2.4 Upload Failure: Format or Decompression Bomb
- **Symptom:** HTTP 400 with `Validation failed: File header does not match any recognized format` or `Raster dimensions exceed allowable limit`.
- **Cause:**
  - File is an unsupported format or corrupted stream.
  - Image exceeds $8192 \times 8192$ or $67.1 \text{ M}$ pixels (decompression protection).
- **Solution:**
  - Ensure imagery is in standard GeoTIFF (`.tif`), TIFF, PNG, or JPEG.
  - Sub-sample large regional mosaics before uploading.

### 2.5 Temporal Alignment Failure
- **Symptom:** HTTP 400 with `ALIGNMENT_FAILURE: Non-overlapping spatial bounds`.
- **Cause:** Pre- and post-event images share different regions with zero geographic intersection.
- **Solution:**
  - SatQuery AI intentionally fails closed to prevent hallucinating changes between disjoint scenes.
  - Ensure T1 and T2 rasters share overlapping spatial bounds in a valid coordinate reference system.

### 2.6 Report Generation Fails
- **Symptom:** HTTP 500 when requesting `/pdf` or `/package`.
- **Cause:** Missing ReportLab dependency or write permission in artifact cache.
- **Solution:**
  - Ensure `reportlab` is installed: `pip install reportlab>=4.0.0`.
  - Check directory permissions on `./artifacts` and `./data/storage`.
