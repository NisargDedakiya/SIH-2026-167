# Failure Modes, Limitations & Domain Transfer Analysis

## 1. Known Failure Modes

### 1.1 Sub-10m Spatial Features
- **Description:** Small vehicles, narrow footpaths, and residential rooftop antennas cannot be accurately resolved.
- **Physical Reason:** Sentinel-2 optical bands have a minimum Ground Sampling Distance (GSD) of 10 meters per pixel.
- **Mitigation:** The agent returns a clarification warning when queries ask for sub-pixel objects on satellite imagery.

### 1.2 Extreme Speckle Noise in SAR Acquisitions
- **Description:** High-relief mountainous terrain causes geometric distortions (foreshortening, layover, radar shadow) and multiplicative speckle.
- **Mitigation:** SAR preprocessor applies $10\log_{10}$ decibel transformation and 1%-99% percentile clipping before passing features to the cross-modal attention projections.

### 1.3 Seasonal & Phenological Reflectance Shifts
- **Description:** Deciduous forest in winter exhibits low NDVI and spectral characteristics resembling transitional shrubs or sparse vegetation.
- **Mitigation:** Model confidence variance reflects seasonal ambiguity; dual-temporal analysis (Phase 5) is recommended for unambiguous land cover typing.

---

## 2. Domain Transfer to Indian Space Context (Cartosat / RISAT)
BigEarthNet v2.0 is based on European Sentinel-1/2 acquisitions. To transfer to ISRO's Cartosat-2S and RISAT platforms:
1. **Resolution Difference:** Cartosat-2S offers sub-meter panchromatic/multi-spectral imagery (0.65m), whereas Sentinel-2 is 10m. Fine structures appear much sharper.
2. **SAR Wavelength:** RISAT-1 operates in C-band (similar to Sentinel-1), while RISAT-2/2B operates in X-band. X-band exhibits higher surface sensitivity and reduced canopy penetration compared to C-band.
3. **Transferability Strategy:** SatQuery's cross-attention LoRA architecture is designed so that future ISRO-specific adapters can be trained on Cartosat/RISAT patches and swapped dynamically via `artifacts/models/` without recompiling the application or modifying agent logic.
