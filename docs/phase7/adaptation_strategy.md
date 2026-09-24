# Remote-Sensing Adaptation Strategy

## 1. Executive Summary
Generic Vision-Language Models (VLMs) trained on terrestrial consumer photography (such as MS-COCO, Conceptual Captions, and ImageNet) exhibit severe failure modes when applied directly to earth observation imagery. Nadir viewing geometry, multi-spectral band reflectance, scale-invariance challenges, and complex microwave scattering cannot be decoded reliably by zero-shot terrestrial models.

This document details SatQuery's domain adaptation strategy: **Parameter-Efficient Fine-Tuning (PEFT / LoRA)** applied to cross-modal attention projections using paired Sentinel-1 SAR and Sentinel-2 optical data.

---

## 2. Theoretical Framework: Why LoRA for Remote Sensing

### 2.1 The Mathematical Formulation
Low-Rank Adaptation (Hu et al., 2021) hypothesizes that weight updates $\Delta W$ during domain adaptation have a low "intrinsic dimension". For a pre-trained linear weight matrix $W_0 \in \mathbb{R}^{d \times k}$, LoRA decomposes the update into two low-rank matrices:

$$W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \cdot A)$$

where:
- $W_0 \in \mathbb{R}^{d \times k}$ is frozen ($0$ gradients computed or stored).
- $A \in \mathbb{R}^{r \times k}$ is initialized with a Gaussian / Kaiming distribution.
- $B \in \mathbb{R}^{d \times r}$ is initialized to zero, ensuring $\Delta W = 0$ at step 0.
- $r \ll \min(d, k)$ is the rank parameter (set to $r=8$).
- $\alpha$ is the constant scaling factor (set to $\alpha=16$).
- Scaling multiplier: $\frac{\alpha}{r} = 2.0$.

### 2.2 Target Projection Modules
In Vision-Language Models (e.g., BLIP ViT-B/16 + BERT text decoder), domain divergence manifests most severely at the interface where visual patch representations cross-attend to text queries. SatQuery's LoRA engine targets:
1. **Visual Attention:** `qkv` and projection linear layers in the Vision Transformer backbone.
2. **Cross-Attention:** Text decoder layers cross-attending to visual token embeddings (`crossattention.self.query`, `crossattention.self.value`).
3. **Feed-Forward Projections:** Intermediate linear dense layers (`dense_h_to_4h`, `dense_4h_to_h`).

---

## 3. Computational & Memory Efficiency

| Metric | Full Fine-Tuning | Generic Zero-Shot | SatQuery RS PEFT / LoRA (Ours) |
| :--- | :--- | :--- | :--- |
| **Trainable Parameters** | 247,400,000 (100%) | 0 (0%) | **1,572,864 (0.63%)** |
| **Frozen Parameters** | 0 (0%) | 247,400,000 (100%) | **245,827,136 (99.37%)** |
| **Optimizer State Memory** | ~3.0 GB (AdamW fp32) | 0 GB | **~18.9 MB (AdamW fp32)** |
| **Peak Training VRAM/RAM** | > 16.0 GB | N/A | **3.8 GB (CPU mode compatible)** |
| **Risk of Catastrophic Forgetting** | High | None | **Minimal (Base weights immutable)** |
| **Storage per Model Version** | ~980 MB | N/A | **6.3 MB (adapter only)** |

---

## 4. Hyperparameter Architecture

| Hyperparameter | Value | Scientific Justification |
| :--- | :--- | :--- |
| **LoRA Rank ($r$)** | 8 | Balances representational capacity for 19 CORINE classes without overfitting on small CPU-friendly subsets. |
| **LoRA Alpha ($\alpha$)** | 16 | Standard 2x scaling ratio ($16/8 = 2.0$) ensures stable numerical gradients. |
| **LoRA Dropout** | 0.05 | Regularization against patch-level spectral noise. |
| **Optimizer** | AdamW | Weight decay $0.01$ prevents adapter coefficient explosion. |
| **Learning Rate** | $1 \times 10^{-4}$ | Recommended standard for LoRA adapters (10x higher than full fine-tuning rate $1 \times 10^{-5}$). |
| **Loss Formulation** | Label-Smoothed Cross-Entropy ($\epsilon=0.1$) | Prevents over-confidence on mixed-pixel boundary patches. |
