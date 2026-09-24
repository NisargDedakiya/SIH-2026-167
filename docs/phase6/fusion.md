# Phase 6: Cross-Modal Feature Fusion & Disagreement Analysis

## 1. Feature Fusion
The fusion engine combines normalized optical features and log-calibrated SAR features:
- **Modality Weighting**: Computes relative visual information content from signal entropy.
- **Physical Property Extraction**:
  - **Water Bodies**: Low optical NIR reflectance + very low SAR specular backscatter (both agree).
  - **Urban Structures**: Geometric building shapes in optical + intense dihedral double-bounce in SAR (strong complementary agreement).
  - **Vegetation / Forests**: High NDVI in optical NIR/Red + moderate volume scattering in SAR cross-pol (VH/HV).
  - **Cloud Infiltration**: High optical reflectance without ground context + continuous ground backscatter penetration in SAR (modality disagreement / optical degraded).

---

## 2. Modality Disagreement Taxonomy

| Status | Trigger Condition | Physical Interpretation |
|---|---|---|
| `AGREEMENT` | Optical spectral signature and SAR backscatter concur on target class | Water, flat terrain, dense urban confirmed by both sensors. |
| `PARTIAL_AGREEMENT` | Target detected primarily in one sensor with secondary verification in the other | Sparse vegetation, seasonal crops, sub-pixel structures. |
| `DISAGREEMENT` | Physical response diverges sharply due to atmospheric or surface properties | Cloud cover masking optical while SAR penetrates; smooth water vs dark oil slick. |
| `INSUFFICIENT_EVIDENCE` | High nodata coverage or extreme noise | Low SNR, shadow masking in steep terrain. |
