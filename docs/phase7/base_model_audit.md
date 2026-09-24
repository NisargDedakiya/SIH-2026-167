# Phase 7: Base Model Audit & Adaptation Target Analysis

## 1. Base Model Audit

| Attribute | Specification |
|---|---|
| **Model Name** | `Salesforce/blip-vqa-base` |
| **Model Version / Revision** | `v1.0.0` / `main` |
| **Architecture Family** | Vision Transformer + Cross-Attention Language Decoder (BLIP) |
| **Vision Encoder** | ViT-B/16 (12 transformer layers, 768 hidden dim, 12 heads, patch size 16x16) |
| **Language Decoder** | 12-layer Transformer Text Decoder (BERT architecture initialization) |
| **Total Parameter Count** | $\approx 385\text{M}$ parameters |
| **Input Resolution** | $384 \times 384$ pixels (normalized 3-channel RGB/projected multispectral) |
| **Supported Image Formats** | PIL Image, GeoTIFF normalized to 8-bit dynamic range, NumPy float32 arrays |
| **Inference Memory Footprint** | $\approx 1.5\text{ GB}$ (FP32 on CPU) / $\approx 800\text{ MB}$ (FP16/INT8) |
| **License** | BSD 3-Clause (Permissive open-source research and commercial use) |
| **Training Interface** | PyTorch `nn.Module` + Hugging Face `transformers` / `peft` |
| **LoRA Compatibility** | Native support; targets cross-attention projection layers (`q_proj`, `v_proj`) |

---

## 2. Current SatQuery Integration
- Instantiated in `backend/app/ai/models/vqa/rs_vqa_adapter.py` as `RsVqaModel`.
- Registered in `ModelRegistry` as the default model for task `visual_question_answering`.
- Inputs preprocessed via `RemoteSensingPreprocessor.read_and_normalize_bands` (2%–98% percentile contrast stretching).

---

## 3. Pre-Adaptation Limitations (The "Generic VLM" Gap)
1. **Nadir Geometry Deficit**:
   Pre-trained on standard horizontal-view consumer photography (COCO, Visual Genome). Lacks native understanding of orthorectified top-down nadir geometry, high spatial resolution scales, and aerial building footprints.
2. **Spectral Semantics Blindspot**:
   Treats images as natural photographic RGB; lacks comprehension of multispectral bands (NIR, Red Edge, SWIR) and radiometric properties (NDVI, vegetation vigor, moisture stress).
3. **Remote-Sensing Terminology Gap**:
   Fails or hallucinates when asked domain-specific queries containing terms such as "impervious surface", "alluvial plain", "CORINE land cover", "VV/VH polarimetric backscatter", "GSD", or "agricultural parcels".

---

## 4. Primary Adaptation Target
- **Target Component**: Single-Image Remote-Sensing Vision-Language Model (`satquery-rs-v1`).
- **Adaptation Strategy**: Parameter-Efficient Fine-Tuning (LoRA) on remote-sensing instruction pairs derived from BigEarthNet v2.0 land-cover semantics and VRSBench/RSVQA visual question answering.
- **Scope Boundary**: Specialist models for visual grounding (Phase 4), change detection (Phase 5), and optical-SAR fusion (Phase 6) remain independent modular specialists.
