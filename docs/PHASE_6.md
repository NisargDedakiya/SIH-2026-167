# Phase 6 — Optical + SAR Cross-Modal Intelligence

## Overview & SIH Alignment
Phase 6 implements the **Optical + SAR Cross-Modal Intelligence Subsystem** for SatQuery AI, directly fulfilling the core Smart India Hackathon (SIH Problem 26167) requirement for joint multimodal interpretation of co-registered Optical/Multispectral (e.g., Cartosat-2S, Sentinel-2) and Synthetic Aperture Radar (e.g., RISAT-1/2, Sentinel-1) image pairs:
> *"Optical and SAR have fundamentally different imaging characteristics. The system must co-register and jointly reason across paired optical and SAR imagery, preserve multispectral bands and raw SAR complex backscatter (dB scale), extract cross-modal spatial evidence, report explicit modality contributions and physical disagreements, and provide verifiable cross-modal VQA and object grounding."*

---

## Technical Invariant: SAR is NOT an RGB Image
A foundational architectural principle of SatQuery AI:
- **Zero Raw RGB Concatenation**: SAR imagery is never cast to a naive 8-bit RGB image or concatenated as an extra optical channel.
- **Physical Preprocessing**: SAR channels undergo radiometric calibration, $10 \cdot \log_{10}(\text{amplitude}^2 + \epsilon)$ dB log-scaling, and 1%–99% percentile speckle clipping to preserve structural backscatter dynamics (double-bounce, surface roughness, volume scattering).
- **Dual Specialist Encoders**: Separate Optical and SAR encoders project modality-specific representations into a shared latent space before cross-attention feature fusion.

---

## System Architecture

```text
User Query: "Analyze both sensors for water bodies and flood inundation."
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   SATQUERY AGENT ROUTER   │
                        │ - Optical-SAR Pair Match  │
                        │ - Cross-Modal Intent      │
                        │ - CapabilityResolver      │
                        └─────────────┬─────────────┘
                                      │ Task: CROSS_MODAL_ANALYSIS
                                      ▼
     ┌─────────────────────────────────────────────────────────────┐
     │           CROSS-MODAL SUBSYSTEM (3-Stage Modular)           │
     │                                                             │
     │  Stage A: Specialist Modality Encoders                      │
     │  ┌──────────────────────┐       ┌────────────────────────┐  │
     │  │   Optical Encoder    │       │      SAR Encoder       │  │
     │  │ - 4+ Spectral Bands  │       │ - dB Log-Scale ($10\log$)│  │
     │  │ - Reflectance Norm   │       │ - Speckle Percentile   │  │
     │  │ - Cloud/Shadow Mask  │       │ - Pol (VV/VH/HH/HV)    │  │
     │  └──────────┬───────────┘       └───────────┬────────────┘  │
     │             │                               │               │
     │             └───────────────┬───────────────┘               │
     │                             ▼                               │
     │  Stage B: Cross-Modal Feature Fusion                        │
     │  ┌──────────────────────────────────────────────────────┐   │
     │  │ - Cross-Modal Attention & Modality Contribution       │   │
     │  │ - Physical Agreement / Disagreement Matrix Engine    │   │
     │  │   (AGREEMENT, PARTIAL_AGREEMENT, DISAGREEMENT)        │   │
     │  └──────────────────────────┬───────────────────────────┘   │
     │                             ▼                               │
     │  Stage C: Task-Specific Reasoning & Grounding               │
     │  ┌──────────────────────────────────────────────────────┐   │
     │  │ - Joint Multimodal Interpretation                    │   │
     │  │ - Cross-Modal VQA & Grounding Bounding Boxes         │   │
     │  │ - Multimodal Entropy-Variance Confidence             │   │
     │  └──────────────────────────────────────────────────────┘   │
     └─────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │   OUTPUT & AUDIT TRACE    │
                     │ - Joint Natural Lang Answer │
                     │ - Optical Summary (Cyan)  │
                     │ - SAR Summary (Amber)     │
                     │ - Disagreement Explanation│
                     │ - Evidence Bounding Boxes │
                     │ - Non-Destructive Trace   │
                     └───────────────────────────┘
```

---

## Technical Invariants Preserved

1. **Non-Destructive Co-Registration**:
   - Original ingested satellite rasters are strictly read-only and never modified on disk or in object storage.
   - When rasters require alignment (differing dimensions, pixel spacing, or coordinate transforms), SAR is non-destructively reprojected to Optical's grid using bilinear interpolation in memory.
2. **Strict Modality Validation**:
   - Pair registration enforces that exactly one image is Optical/Multispectral and one is Synthetic Aperture Radar.
   - Optical+Optical or SAR+SAR pairings are strictly rejected with descriptive error codes.
3. **Explicit Modality Disagreement Reporting**:
   - When optical reflectance contradicts SAR backscatter (e.g., cloud cover obscuring optical while SAR penetrates, or smooth asphalt displaying dark SAR specular reflection but high optical albedo), the system explicitly reports a structured `ModalityDisagreement` rather than hallucinating consistency.
4. **Multimodal Entropy-Variance Confidence**:
   - Computes weighted confidence scores factoring in optical clarity, SAR speckle variance, and cross-modal agreement state.
5. **Zero Regressions**:
   - Single-image VQA, Captioning, Object Grounding, and Phase 5 Bi-Temporal Change Detection remain 100% operational with 88 passing backend tests.

---

## Data Model & Database Schema

The database schema is extended with:
- **`optical_sar_pairs` Table (`OpticalSARPairModel`)**:
  - `id`: UUID primary key
  - `optical_image_id`: UUID foreign key referencing `images.id`
  - `sar_image_id`: UUID foreign key referencing `images.id`
  - `optical_modality`: String ("optical", "multispectral")
  - `sar_modality`: String ("sar")
  - `optical_sensor` & `sar_sensor`: String names (e.g., "Cartosat-2S", "RISAT-1")
  - `spatial_compatibility`: String ("COMPATIBLE", "INSUFFICIENT_OVERLAP", "INCOMPATIBLE")
  - `registration_status`: String ("REGISTERED", "ALIGNED", "FAILED")
  - `validation_status`: String ("VALID", "INVALID")
  - `overlap_ratio`: Float (0.0 to 1.0)
  - `alignment_method`: String ("bilinear_resampling", "native_grid")
  - `alignment_metadata`: JSON dictionary of affine parameters and scale factors
  - `validation_report`: Full stored JSON validation output
- **`analysis_jobs` Table Migration**:
  - Automatically migrated with `cross_modal_pair_id` (UUID foreign key referencing `optical_sar_pairs.id`).

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/cross-modal/pairs` | Register and validate a new Optical-SAR image pair |
| `GET` | `/api/v1/cross-modal/pairs` | List registered Optical-SAR pairs with metadata and overlap |
| `GET` | `/api/v1/cross-modal/pairs/{pair_id}` | Retrieve pair details, alignment state, and sensor attributes |
| `POST` | `/api/v1/cross-modal/pairs/{pair_id}/validate` | Trigger explicit geospatial and modality re-validation |
| `POST` | `/api/v1/cross-modal/analyze` | Run full cross-modal analysis, joint reasoning, and grounding |
| `POST` | `/api/v1/analysis/cross-modal` | Unified analysis endpoint for joint optical-SAR reasoning |
| `POST` | `/api/v1/analysis/cross-modal-vqa` | Dedicated cross-modal VQA endpoint |
| `POST` | `/api/v1/analysis/cross-modal-grounding` | Dedicated cross-modal spatial bounding box grounding |
| `GET` | `/api/v1/analysis/{id}/cross-modal-evidence` | Retrieve localized cross-modal spatial evidence regions |
