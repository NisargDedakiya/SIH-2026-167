# Model Card: SatQuery-RS-v1

## Model Details
- **Model Name:** `satquery-rs-v1`
- **Model Version:** 1.0.0
- **Model Type:** Parameter-Efficient Vision-Language Adapter (PEFT / LoRA)
- **Base Architecture:** `Salesforce/blip-vqa-base` (ViT-B/16 Vision Transformer + BERT Cross-Attention Decoder)
- **Primary Modality:** Dual-Modal Optical & Synthetic Aperture Radar (SAR) Remote Sensing Imagery
- **Release Date:** September 2026
- **Developer:** SatQuery AI Team (ISRO SIH Problem Statement 26167)
- **Licence:** Apache 2.0 (Code) / ODC-By v1.0 (Dataset Provenance)

---

## Intended Use
### Primary Intended Uses
1. **Satellite Visual Question Answering:** Natural-language queries regarding land cover, infrastructure presence, water bodies, and vegetation health in satellite imagery.
2. **Remote-Sensing Scene Captioning:** Generating structured, domain-adapted descriptions of multi-spectral optical and microwave SAR acquisitions.
3. **Agentic Specialist Integration:** Serving as the default visual question answering specialist tool inside the SatQuery multi-agent analytical system.

### Out-of-Scope Uses
- Real-time tactical military targeting without secondary human analyst verification.
- Micro-object identification (< 10m spatial scale) on low-resolution imagery.
- Direct medical or non-geospatial vision-language tasks.

---

## Training Data & Provenance
- **Dataset:** BigEarthNet v2.0 (Sentinel-1 C-SAR & Sentinel-2 MSI Paired Benchmark)
- **Geographic Coverage:** Western and Central Europe (10 national territories, multiple climate zones)
- **Nomenclature:** CORINE Land Cover (CLC) 19-class taxonomy
- **Preprocessing:** 2%-98% percentile optical contrast stretching; $10\log_{10}$ SAR decibel calibration with 1%-99% speckle suppression.

---

## Technical Specifications & Hyperparameters
- **Trainable Parameters:** 1,572,864 (0.63% of base model)
- **Frozen Parameters:** 245,827,136 (99.37% of base model)
- **LoRA Rank ($r$):** 8
- **LoRA Alpha ($\alpha$):** 16
- **LoRA Dropout:** 0.05
- **Optimizer:** AdamW ($\beta_1=0.9, \beta_2=0.999$, weight decay $0.01$)
- **Learning Rate:** $1 \times 10^{-4}$ with linear warmup
- **Adapter Weight Checkpoint Size:** 6.3 MB

---

## Performance Summary

| Benchmark | Baseline Score | Adapted Score (`satquery-rs-v1`) | Absolute Gain |
| :--- | :--- | :--- | :--- |
| **VRSBench Accuracy** | 0.0% | **80.0%** | **+80.0%** |
| **VRSBench Token F1** | 0.157 | **0.800** | **+0.643** |
| **RSVQA Accuracy** | 20.0% | **60.0%** | **+40.0%** |

---

## Bias, Risks & Limitations
1. **Regional Biases:** Training data consists primarily of European bioclimatic regions; arid, tropical monsoon, or Himalayan terrain may experience reduced classification confidence.
2. **Sensor Resolution Limits:** Objects smaller than the 10m Sentinel-2 pixel size cannot be resolved accurately.
3. **Cloud Cover Interference:** Optical queries over heavy cloud cover must be routed to SAR specialist pipelines rather than optical VQA.
