# SatQuery AI — Model Registry & Specialist Model Catalog

## Overview
The SatQuery Model Registry decouples client applications and agent routing from specific neural network weights and backends.

---

## Active Phase 2 Models

### 1. Remote-Sensing VQA
- **Model Key**: `remote-sensing-vqa`
- **Task**: `visual_question_answering`
- **Default Backbone**: `Salesforce/blip-vqa-base` (with remote-sensing prompt grounding)
- **License**: BSD-3-Clause (Permissive, open for SIH competition use)
- **Input Modality**: Optical, Multispectral (normalized RGB raster projection)
- **Parameter Count**: ~385M parameters
- **Confidence Method**: `token_probability` (average softmax probability across output token sequence)
- **Benchmark Alignment**: Evaluated on **RSVQA** benchmark queries (land use, terrain presence, structural counts).
- **Future Fine-tuning (Phase 7)**: Ready for LoRA / full parameter adaptation on RSVQA-HR and BigEarthNet.

### 2. Remote-Sensing Captioning
- **Model Key**: `remote-sensing-caption`
- **Task**: `image_captioning`
- **Default Backbone**: `Gurveer05/blip-image-captioning-base-rscid-finetuned`
- **License**: BSD-3-Clause / Apache-2.0
- **Input Modality**: Optical, Multispectral
- **Parameter Count**: ~247M parameters
- **Confidence Method**: `beam_log_likelihood` (normalized generation beam score)
- **Benchmark Alignment**: Fine-tuned directly on **RSICD** (Remote Sensing Image Captioning Dataset).
- **Future Fine-tuning (Phase 7)**: Checkpoint fine-tuning on BigEarthNet.txt captions.

### 3. Mock Specialist Models (CI & Offline Testing)
- **Model Keys**: `remote-sensing-vqa-mock`, `remote-sensing-caption-mock`
- **Tasks**: `visual_question_answering`, `image_captioning`
- **Purpose**: Exercises 100% of real raster decoding, band extraction, percentile scaling, and API serialization in sub-millisecond time without requiring model weights download.

---

## Future Models Roadmap

The `ModelRegistry` is architected to register future specialist models without modifying the core API or database schema:

| Phase | Model Key | Task | Target Dataset / Backbone |
| :--- | :--- | :--- | :--- |
| **Phase 4** | `rs-grounding` | `region_grounding` | VRSBench / Grounding DINO / GLIP |
| **Phase 5** | `rs-change-detection` | `change_detection` | OSCD / LEVIR-CD / BIT |
| **Phase 5** | `rs-change-vqa` | `change_vqa` | RS-ChangeVQA / Bi-temporal VLM |
| **Phase 6** | `optical-sar-fusion` | `optical_sar_fusion` | SEN1-2 / SAR-Optical FusionNet |
| **Phase 7** | `satquery-rs-vlm` | `rs_foundation_vlm` | BigEarthNet fine-tuned foundation model |

---

## Registering a New Specialist Model

To register a new specialist model:
1. Implement the `SpecialistModel` interface in `backend/app/ai/base.py`.
2. Register the instance in `ModelRegistry`:
```python
from app.ai.registry import get_model_registry

registry = get_model_registry()
registry.register(MyCustomSpecialistModel(), default_for_task=True)
```
