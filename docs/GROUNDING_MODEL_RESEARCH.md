# SatQuery AI — Remote-Sensing Grounding Model Selection Report

## 1. Executive Summary & Problem Framing
In ISRO SIH Problem 26167, the multimodal vision-language assistant must ground textual referring expressions (e.g. *"Highlight the water body"*, *"Where are the building clusters?"*, *"Locate the runway"*) into verified visual regions.

Visual grounding in remote sensing presents unique domain challenges compared to general web imagery:
1. **Extreme Scale Variation**: Objects range from small structures (vehicles, storage tanks, houses) to regional expanses (rivers, forests, agricultural zones).
2. **Nadir / Overhead Perspectives**: Absence of canonical orientation, horizon, or camera viewpoint biases.
3. **Dense Clustering**: Urban buildings and agricultural parcels appear in dense repetitive lattices.
4. **Coordinate Integrity**: Predicted coordinates must faithfully reproject from resized model inputs back to original multi-megapixel rasters and native coordinate reference systems (CRS).

---

## 2. Model Evaluation Matrix

| Attribute | **Candidate A: OWL-ViT / OWLv2** (Google) | **Candidate B: Grounding DINO** (IDEA-Research) | **Candidate C: VRSBench Grounding** | **Candidate D: Remote-Sensing ResNet/ViT + Faster R-CNN** |
| :--- | :--- | :--- | :--- | :--- |
| **Model Family** | Open-vocabulary detector (CLIP Vision Transformer backbone) | Open-set object detector (Swin/BERT cross-attention) | Specialized remote-sensing referring detector | Closed-vocabulary detector with text classification |
| **Remote-Sensing Compatibility** | **High**: Zero-shot transfer from CLIP pretraining exhibits strong generalization on satellite features (water bodies, vegetation, buildings, runways). | **High**: High precision on aerial benchmarks (DOTA/DIOR/VRSBench) with fine-grained bounding boxes. | **Native**: Specifically fine-tuned on aerial imagery & referring expressions. | **Low**: Limited to predetermined fixed class catalogs; fails on free-form natural language. |
| **Input Format** | RGB Raster (e.g., 768×768 to 1024×1024) + Text Query Array | RGB Raster (e.g., 800×800) + Text Prompt String (`"water body . building ."`) | RS Raster + Referring Expression Text | Raster + predefined integer labels |
| **Output Type** | Normalized bounding boxes `[x1, y1, x2, y2]` + class logits + confidence | Normalized boxes `[cx, cy, w, h]` + phrases + confidence | Bounding boxes + segmentation masks | Bounding boxes + class IDs |
| **License** | **Apache 2.0** (Open Commercial / Research) | **Apache 2.0** | Non-commercial / Research-only variants | Apache 2.0 |
| **GPU Requirements** | 2.5 GB – 4.0 GB VRAM (Inference runs comfortably on CPU or CUDA) | 3.5 GB – 6.0 GB VRAM | 8.0 GB – 16.0 GB VRAM | 2.0 GB VRAM |
| **Inference Latency** | **Fast**: ~80–180ms (GPU) / ~1.2s (CPU) | ~120–280ms (GPU) / ~2.5s (CPU) | ~450–1200ms (GPU) / slow on CPU | ~60ms (GPU) |
| **HuggingFace Integration** | **Native**: `transformers.OwlViTForObjectDetection` (zero third-party binary dependencies) | Requires external repo / custom CUDA ops (`groundingdino-py`) | Custom repository & weights | Standard `torchvision` |
| **Fine-Tuning Possibility** | **High**: Standard HuggingFace Trainer with RS datasets (DOTA, DIOR, NWPU, VRSBench). | High, but complex custom loss implementations. | Medium (custom codebases). | High |
| **Evidence Output** | Multi-region bounding boxes, confidence score per box, crop generation | Multi-region bounding boxes, confidence per box | Multi-region boxes & masks | Bounding boxes |

---

## 3. Selection Recommendation & Strategy

### Primary Selected Architecture: **Open-Vocabulary Remote-Sensing Grounding Adapter (OWLv2 / OwlViT)**
**Rationale**:
1. **Zero Proprietary CUDA Compilation**: Natively integrated in standard `transformers` library, eliminating installation failures on standard Windows/Linux developer environments without specialized C++ build toolchains.
2. **True Open-Vocabulary Flexibility**: Seamlessly handles arbitrary user expressions (*"water body"*, *"dense residential buildings"*, *"river tributary"*, *"aircraft on tarmac"*, *"agricultural fields"*).
3. **Calibrated Per-Region Confidence**: Direct sigmoid logits produce reliable, individual confidence scores for every detected spatial region.
4. **Dual Execution Engine (Hybrid Native + Fast Mock)**:
   - When `AI_USE_MOCK=False`: Leverages `google/owlvit-base-patch32` (or configured checkpoint) with remote-sensing preprocessing and band normalization.
   - When `AI_USE_MOCK=True` (or offline/CI mode): Employs deterministic remote-sensing feature-space localization to guarantee 100% reproducible tests without multi-gigabyte downloads.
5. **Phase 4 & 5 Extensibility**: Generates bounding boxes, crop artifacts, polygonal segmentation representations, and full CRS coordinate transforms needed for bi-temporal change detection in Phase 5.
