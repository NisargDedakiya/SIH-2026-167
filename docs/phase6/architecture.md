# Phase 6: System Architecture & Design Principles

## 1. Architectural Philosophy: SAR is NOT an RGB Image

Standard computer vision approaches frequently treat multimodal satellite images as multi-channel image stacks, naively concatenating SAR amplitude channels onto RGB channels. In remote sensing, this leads to severe domain collapse and uninterpretable models:
- **Optical sensors** measure surface spectral reflectance across visible and infrared wavelengths governed by molecular electronic transitions and chlorophyll absorption.
- **Synthetic Aperture Radar (SAR)** actively emits coherent microwave pulses (e.g., C-band, L-band, X-band) and records the amplitude and phase of backscattered radiation governed by dielectric permittivity, micro-roughness, moisture, and macroscopic target geometry.

SatQuery AI's architecture enforces strict physical separation:
1. **Specialist Modality Encoders**: Dedicated preprocessing pipelines honoring the distinct physics of each sensor.
2. **Intermediate Latent Projection**: Modality-specific feature tokens projected into a common embedding space.
3. **Cross-Attention Fusion**: Learned cross-modal attention maps where optical context queries SAR geometry and vice-versa.
4. **Physical Disagreement Engine**: Explicit detection and reasoning when physical evidence from the two modalities diverges.

---

## 2. The 3-Stage Modular Pipeline

```
Raw Optical GeoTIFF ────► Optical Encoder (Multispectral Normalization) ──┐
                                                                           ├─► Cross-Modal Fusion ─► Task Reasoning
Raw SAR GeoTIFF ────────► SAR Encoder (dB Log-Scale + Speckle Clip)    ──┘
```

### Stage A: Specialist Modality Encoders
- **Optical Encoder**: Preserves all multispectral bands, applies 2%–98% percentile contrast normalization, and filters nodata/saturation artifacts.
- **SAR Encoder**: Ingests single- or multi-polarization complex/amplitude data (VV, VH, HH, HV). Applies radiometric calibration to convert DN to radar backscatter coefficient $\sigma^0$, converts to decibel scale ($10 \cdot \log_{10}(\text{amplitude}^2 + \epsilon)$), and applies 1%–99% speckle suppression.

### Stage B: Cross-Modal Feature Fusion
- Cross-attention transformer blocks where optical tokens query SAR spatial tokens.
- Generates fused representation $\mathbf{Z}_{\text{fused}} = \text{LayerNorm}(\mathbf{Z}_{\text{opt}} + \text{Attention}(\mathbf{Z}_{\text{opt}}, \mathbf{Z}_{\text{sar}}, \mathbf{Z}_{\text{sar}}))$.
- Computes modality contribution factors and evaluates physical consistency across 4 states:
  - `AGREEMENT`: Both sensors confirm identical geographic phenomenon.
  - `PARTIAL_AGREEMENT`: One sensor provides primary confirmation while the second provides complementary secondary context.
  - `DISAGREEMENT`: Physics-governed divergence (e.g., cloud cover obscuring optical while SAR penetrates; smooth asphalt exhibiting low SAR backscatter but high optical reflectance).
  - `INSUFFICIENT_EVIDENCE`: Low signal-to-noise or excessive nodata.

### Stage C: Task-Specific Reasoning & Grounding
- Synthesizes findings for three dedicated downstream tasks:
  1. `cross_modal_analysis`: Joint interpretation report with individual modality contribution summaries.
  2. `cross_modal_vqa`: Question-answering specifically addressing cross-sensor phenomena.
  3. `cross_modal_grounding`: Extraction of geo-referenced spatial bounding boxes tagged with the contributing modality (`optical`, `sar`, or `both`).
