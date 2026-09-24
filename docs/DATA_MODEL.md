# SatQuery AI — Data Model Specification

The database utilizes PostgreSQL with the PostGIS extension. The data model is partitioned into core immutable image records and extensible metadata.

---

## 1. Entity-Relationship Diagram

```
┌────────────────────────────────────────┐
│                 images                 │
├────────────────────────────────────────┤
│ id: UUID (PK)                          │
│ original_filename: VARCHAR(255)        │
│ object_key: VARCHAR(512)               │
│ preview_key: VARCHAR(512)              │
│ mime_type: VARCHAR(64)                 │
│ file_format: VARCHAR(32)               │
│ file_size: BIGINT                      │
│ checksum: VARCHAR(64)                  │
│ width: INTEGER                         │
│ height: INTEGER                        │
│ band_count: INTEGER                    │
│ dtype: VARCHAR(32)                     │
│ crs: VARCHAR(255) (nullable)           │
│ epsg_code: INTEGER (nullable)          │
│ resolution_x: FLOAT (nullable)         │
│ resolution_y: FLOAT (nullable)         │
│ bounds: JSONB (nullable)               │
│ transform: JSONB (nullable)            │
│ nodata: FLOAT (nullable)               │
│ acquisition_time: TIMESTAMPTZ (null)   │
│ sensor: VARCHAR(128) (nullable)        │
│ modality: VARCHAR(64) [default: unknown]│
│ is_geospatial: BOOLEAN                 │
│ validation_status: VARCHAR(32)         │
│ created_at: TIMESTAMPTZ                │
│ updated_at: TIMESTAMPTZ                │
└───────────────────┬────────────────────┘
                    │ 1
                    │
                    │ 1..N
┌───────────────────▼────────────────────┐
│             image_metadata             │
├────────────────────────────────────────┤
│ id: UUID (PK)                          │
│ image_id: UUID (FK -> images.id)       │
│ metadata_json: JSONB                   │
│ created_at: TIMESTAMPTZ                │
└────────────────────────────────────────┘
```

---

## 2. Table Specifications

### Table: `images`
Stores the fundamental raster characteristics and geospatial properties of every uploaded satellite/remote-sensing file.

- **`id`**: Unique UUID assigned at ingestion time.
- **`original_filename`**: Sanitized name of the source uploaded file.
- **`object_key`**: S3/MinIO key (e.g. `images/{uuid}/original.tif`).
- **`preview_key`**: S3/MinIO key for browser-ready preview (e.g. `images/{uuid}/preview.png`).
- **`mime_type`**: Detected MIME type from binary headers.
- **`file_format`**: Standardized format name (`GeoTIFF`, `TIFF`, `PNG`, `JPEG`).
- **`file_size`**: Size in bytes.
- **`checksum`**: SHA-256 hash for integrity validation and de-duplication.
- **`width`**, **`height`**: Dimensions in pixels.
- **`band_count`**: Number of spectral bands or color channels.
- **`dtype`**: NumPy/Rasterio data type (`uint8`, `uint16`, `float32`, etc.).
- **`crs`**: Coordinate Reference System representation (e.g., `EPSG:4326`, `EPSG:32643`, or WKT string).
- **`epsg_code`**: Parsed numeric EPSG code if available.
- **`resolution_x`**, **`resolution_y`**: Ground Sample Distance (GSD) or pixel resolution.
- **`bounds`**: Georeferenced bounding box (`left`, `bottom`, `right`, `top`).
- **`transform`**: Affine transformation matrix (6 or 9 coefficients).
- **`nodata`**: Value designated for nodata/masked pixels.
- **`acquisition_time`**: Timestamp of satellite sensor capture (nullable).
- **`sensor`**: Satellite instrument/sensor name (e.g., Sentinel-2 MSI, Landsat-8 OLI, nullable).
- **`modality`**: `optical`, `multispectral`, `sar`, or `unknown`.
- **`is_geospatial`**: Boolean flag indicating valid georeferencing.
- **`validation_status`**: `valid`, `warning`, or `error`.
- **`created_at`**, **`updated_at`**: Timestamps.

### Table: `image_metadata`
Extensible key-value store for satellite-specific auxiliary tags, STAC items, EXIF headers, or future model-derived attributes.
- **`id`**: UUID.
- **`image_id`**: Foreign key pointing to `images.id` (with `ON DELETE CASCADE`).
- **`metadata_json`**: Structured JSONB document containing arbitrary nested attributes.
- **`created_at`**: Timestamp.
