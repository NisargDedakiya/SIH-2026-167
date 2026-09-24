# Phase 6: Non-Destructive Alignment & Co-Registration

## 1. Zero-Modification Invariant
Satellite rasters stored in SatQuery AI's object storage are immutable. During cross-modal registration:
- Original Optical GeoTIFF is read-only.
- Original SAR GeoTIFF is read-only.
- All spatial warps and resamplings are computed dynamically in memory or stored under `pair_artifacts/`.

---

## 2. Alignment Mechanics
1. **Target Grid Selection**: The optical raster's spatial grid (CRS, pixel resolution, dimensions) is selected as the canonical reference grid.
2. **Resampling Method**:
   - Continuous backscatter/reflectance uses bilinear resampling (`Resampling.bilinear`).
   - When rasterio warping is invoked, `reproject()` resamples SAR into the optical coordinate frame without pixel degradation.
3. **Cross-Modal Quality Metric**:
   - Optical and SAR have fundamentally different intensity distributions, making normalized cross-correlation (NCC) unreliable.
   - The engine computes an edge-gradient correlation metric (Sobel edge magnitude alignment) to evaluate co-registration quality.
