# Phase 6: Modality Validation & Compatibility Checking

## 1. Validation Logic
Cross-modal pairing enforces strict domain-specific rules:

1. **Modality Check**:
   - Primary raster MUST be recognized as `OPTICAL` (including `MULTISPECTRAL`, `RGB`).
   - Secondary raster MUST be recognized as `SAR` (Synthetic Aperture Radar).
   - If both rasters are Optical $\rightarrow$ Reject with `MODALITY_PAIR_INVALID` (suggest Bi-Temporal Change Detection instead).
   - If both rasters are SAR $\rightarrow$ Reject with `MODALITY_PAIR_INVALID`.
2. **Polarization Extraction**:
   - Analyzes SAR band labels, filenames, and metadata for polarimetric configurations: `VV`, `VH`, `HH`, `HV`, `DUAL_POL`, `QUAD_POL`.
3. **Spatial Overlap Evaluation**:
   - Calculates geographic intersection area relative to smaller bounding box.
   - If overlap $< 5\%$ $\rightarrow$ Mark `INSUFFICIENT_OVERLAP`.
   - If CRSs differ $\rightarrow$ Flag for automated non-destructive reprojection.

---

## 2. API Validation Contract

```json
{
  "valid": true,
  "optical_valid": true,
  "sar_valid": true,
  "spatially_compatible": true,
  "overlap_ratio": 0.942,
  "status_code": "COMPATIBLE",
  "message": "Optical-SAR pair is fully compatible for joint cross-modal reasoning.",
  "optical_modality": "optical",
  "sar_modality": "sar",
  "sar_polarization": "VV",
  "warnings": []
}
```
