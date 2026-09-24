# Phase 6: Multimodal Confidence Estimation

## 1. Multimodal Entropy-Variance Formulation
Cross-modal confidence cannot rely solely on softmax probabilities from a single model. SatQuery AI computes an aggregated score:

$$C_{\text{multimodal}} = w_{\text{opt}} C_{\text{opt}} + w_{\text{sar}} C_{\text{sar}} - \lambda \Delta_{\text{disagreement}}$$

Where:
- $C_{\text{opt}}$ is the optical prediction confidence derived from feature entropy.
- $C_{\text{sar}}$ is the SAR prediction confidence derived from local speckle signal-to-noise ratio.
- $w_{\text{opt}}, w_{\text{sar}}$ are dynamic modality weights based on cloud cover metrics and valid data masks ($w_{\text{opt}} + w_{\text{sar}} = 1$).
- $\Delta_{\text{disagreement}}$ penalizes unexplained physical contradictions while rewarding corroborated observations.

---

## 2. Threshold Calibration
- **High Confidence ($\ge 85\%$)**: Strong spatial corroboration across both modalities.
- **Moderate Confidence ($70\% - 84\%$)**: One modality dominant with acceptable consistency.
- **Cautious Confidence ($< 70\%$)**: Marked disagreement or elevated speckle noise.
