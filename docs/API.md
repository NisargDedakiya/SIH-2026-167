# SatQuery AI — API Specification

Base Path: `/api/v1`

All responses are formatted in structured JSON. Errors use standard RFC 7807 problem details format or clean `{ "detail": "..." }` schemas.

---

## Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `POST` | `/api/v1/images/upload` | Upload & ingest remote-sensing image |
| `GET` | `/api/v1/images/{image_id}` | Retrieve image details and extracted metadata |
| `POST` | `/api/v1/images/{image_id}/validate` | Re-trigger or inspect validation status |
| `GET` | `/api/v1/images/{image_id}/preview` | Download or stream rendered preview image |
| `DELETE` | `/api/v1/images/{image_id}` | Safely delete image record, raw file, and preview |

---

## 1. Health Check
- **Endpoint**: `GET /health`
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "storage": "connected"
}
```

---

## 2. Image Upload
- **Endpoint**: `POST /api/v1/images/upload`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file (`.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`)
- **Response**: `201 Created`
```json
{
  "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
  "filename": "sentinel2_sample.tif",
  "status": "valid",
  "message": "Image uploaded and processed successfully"
}
```

---

## 3. Inspect Image Metadata
- **Endpoint**: `GET /api/v1/images/{image_id}`
- **Response**: `200 OK`
```json
{
  "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
  "filename": "sentinel2_sample.tif",
  "format": "GeoTIFF",
  "size_bytes": 14285714,
  "raster": {
    "width": 4096,
    "height": 4096,
    "bands": 4,
    "dtype": "uint16"
  },
  "geospatial": {
    "is_geospatial": true,
    "crs": "EPSG:32643",
    "epsg": 32643,
    "bounds": {
      "left": 72.1,
      "bottom": 21.1,
      "right": 72.2,
      "top": 21.2
    },
    "resolution": {
      "x": 10.0,
      "y": 10.0
    }
  },
  "validation": {
    "valid": true,
    "warnings": [],
    "errors": []
  }
}
```

---

## 4. Revalidate Image
- **Endpoint**: `POST /api/v1/images/{image_id}/validate`
- **Response**: `200 OK`
```json
{
  "valid": true,
  "warnings": [],
  "errors": [],
  "metadata": { ... }
}
```

---

## 5. Get Image Preview
- **Endpoint**: `GET /api/v1/images/{image_id}/preview`
- **Response**: Binary image stream (`image/png` or `image/jpeg`).

---

## 6. Delete Image
- **Endpoint**: `DELETE /api/v1/images/{image_id}`
- **Response**: `200 OK`
```json
{
  "id": "8f6a7c8b-2d4e-4f1a-b3c5-9e8a7b6c5d4e",
  "deleted": true
}
```
