# Phase 6: Cross-Modal Spatial Grounding

## 1. Task Definition
Cross-Modal Spatial Grounding localizes objects and phenomena that require evidence from either or both sensors:
- Normalized bounding box coordinates `[ymin, xmin, ymax, xmax]`.
- Absolute pixel bounding box `{x1, y1, x2, y2, w, h}`.
- Native CRS geospatial polygon coordinates.
- Attribution tag: `supported_by` set to `"optical"`, `"sar"`, or `"both"`.

---

## 2. Evidence Tagging Criteria
- **`both`**: Feature has clear spectral boundary in optical and sharp dielectric/geometric contrast in SAR (e.g., dual-confirmed urban structure or open reservoir).
- **`optical`**: Feature identified by spectral color/albedo where microwave backscatter is diffuse or uninformative (e.g., subtle soil color difference).
- **`sar`**: Feature identified by radar backscatter despite optical degradation (e.g., structure under cloud or flood water under tree canopy).
