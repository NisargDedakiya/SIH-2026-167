# Phase 6: Optical-SAR Pairs & Data Model

## 1. Domain Concept
An **Optical-SAR Pair** binds two satellite raster assets covering an overlapping geographic region:
- **Optical Image**: Cartosat-2S, Sentinel-2, or high-resolution aerial imagery.
- **SAR Image**: RISAT-1/2, Sentinel-1, or airborne radar imagery.

Unlike temporal pairs where images are ordered chronologically ($T_1 < T_2$), an Optical-SAR pair is an asymmetric sensor binding where images may be near-synchronous or acquired within a reasonable temporal window, with focus on spectral-microwave complementarity.

---

## 2. Relational Database Schema

```sql
CREATE TABLE optical_sar_pairs (
    id VARCHAR(36) PRIMARY KEY,
    optical_image_id VARCHAR(36) NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    sar_image_id VARCHAR(36) NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    optical_modality VARCHAR(32) NOT NULL DEFAULT 'optical',
    sar_modality VARCHAR(32) NOT NULL DEFAULT 'sar',
    optical_sensor VARCHAR(64),
    sar_sensor VARCHAR(64),
    spatial_compatibility VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    registration_status VARCHAR(32) NOT NULL DEFAULT 'UNREGISTERED',
    validation_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    overlap_ratio FLOAT,
    alignment_method VARCHAR(64),
    alignment_metadata JSON,
    validation_report JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP)
);

CREATE INDEX ix_optical_sar_pairs_optical_id ON optical_sar_pairs(optical_image_id);
CREATE INDEX ix_optical_sar_pairs_sar_id ON optical_sar_pairs(sar_image_id);
```

---

## 3. Pair Lifecycle States

1. **`REGISTERED`**: Pair record created, metadata extracted from ingested raster records.
2. **`VALIDATED`**: Modality compatibility verified (exactly one optical and one SAR) and geographic bounding box intersection verified ($>0\%$ overlap).
3. **`ALIGNED`**: In-memory or persisted co-registration performed using bilinear resampling onto optical grid.
4. **`ANALYZED`**: Cross-modal inference completed, with analysis job linked to pair via `cross_modal_pair_id`.
