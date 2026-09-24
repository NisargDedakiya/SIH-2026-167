# Phase 6: Model Selection & Encoder Architectures

## 1. Specialist Encoders

### Optical Encoder (`OpticalEncoder`)
- **Input**: Raw Optical / Multispectral raster $\mathbf{I}_{\text{opt}} \in \mathbb{R}^{H \times W \times C_{\text{opt}}}$ ($C_{\text{opt}} \ge 3$).
- **Normalization**: Percentile contrast stretching (2%–98%) computed per-channel across valid data masks.
- **Output**: Latent token grid $\mathbf{Z}_{\text{opt}} \in \mathbb{R}^{N \times D}$.

### SAR Encoder (`SAREncoder`)
- **Input**: Raw SAR amplitude/intensity raster $\mathbf{I}_{\text{sar}} \in \mathbb{R}^{H \times W \times C_{\text{sar}}}$ with polarization channels.
- **Radiometric Log Transformation**:
  $$\sigma^0_{\text{dB}} = 10 \cdot \log_{10}(\mathbf{I}_{\text{sar}} + 10^{-6})$$
- **Speckle Percentile Clipping**:
  Clips $\sigma^0_{\text{dB}}$ between 1st and 99th percentiles to mitigate speckle noise while preserving dynamic range.
- **Output**: Latent token grid $\mathbf{Z}_{\text{sar}} \in \mathbb{R}^{N \times D}$.

---

## 2. Cross-Modal Fusion Architecture (`CrossModalFusionModel`)
- Implements `CrossModalModel` abstract base class.
- Uses bidirectional cross-attention layers to exchange contextual tokens between optical spectral representations and SAR backscatter representations.
- Supports both production deep neural weights and lightweight fallback mock mode (`mock=True`) for continuous integration testing without GPU overhead.
