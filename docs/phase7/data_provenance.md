# Data Provenance & Dataset Specification

## 1. Executive Overview
To satisfy the ISRO Smart India Hackathon (SIH 2026) requirement for domain-adapted remote-sensing vision-language intelligence, **SatQuery AI** integrates **BigEarthNet v2.0** as its foundational remote-sensing training corpus, alongside **VRSBench** and **RSVQA** as standardized, strictly quarantined evaluation benchmarks.

This document establishes the verified provenance, sensor characteristics, licensing, and geographic lineage of all data utilized in Phase 7.

---

## 2. Training Corpus: BigEarthNet v2.0

### 2.1 Sensor & Modality Specifications
BigEarthNet v2.0 provides dual-modal remote-sensing data across 549,488 image patches collected over 10 European countries (Austria, Belgium, Finland, Ireland, Kosovo, Lithuania, Luxembourg, Portugal, Serbia, and Switzerland).

| Sensor | Constellation | Modality | Spectral Bands / Channels | Ground Sampling Distance (GSD) | Radiometric Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MSI** | Sentinel-2A / 2B | Multi-Spectral Optical | 12 bands (B01-B08, B8A, B09, B11, B12) | 10m (B02-B04, B08)<br>20m (B05-B07, B8A, B11-B12)<br>60m (B01, B09) | 12-bit uint16 (Level-2A BOA Reflectance) |
| **C-SAR** | Sentinel-1A / 1B | Synthetic Aperture Radar | Dual-pol VV, VH (IW mode, Ground Range Detected) | 10m spatial resolution | 16-bit linear backscatter amplitude |

### 2.2 Land Cover Nomenclature: CORINE Land Cover (CLC) 19 Classes
BigEarthNet v2.0 standardizes land cover classification into a 19-class hierarchical nomenclature adapted from the European Environment Agency's CORINE Land Cover 2018 database:

1. **Urban fabric** (continuous and discontinuous urban fabric)
2. **Industrial or commercial units**
3. **Arable land** (non-irrigated arable land and permanently irrigated land)
4. **Permanent crops** (vineyards, fruit trees, berry plantations, olive groves)
5. **Pastures**
6. **Complex cultivation patterns**
7. **Land principally occupied by agriculture, with significant areas of natural vegetation**
8. **Agro-forestry areas**
9. **Broad-leaved forest**
10. **Coniferous forest**
11. **Mixed forest**
12. **Natural grassland and sparsely vegetated areas**
13. **Moors, heathland and sclerophyllous vegetation**
14. **Sclerophyllous vegetation**
15. **Transitional woodland, shrub**
16. **Beaches, dunes, sands**
17. **Inland wetlands** (inland marshes, peatbogs)
18. **Coastal wetlands** (salt marshes, salines, intertidal flats)
19. **Water bodies** (water courses, water bodies, coastal lagoons, estuaries, sea/ocean)

### 2.3 Licensing & Provenance Attributions
- **Licence:** Open Data Commons Attribution License (ODC-By) v1.0.
- **Original Authors:** G. Sumbul, M. Charfuelan, B. Demir, V. Markl (Technische Universität Berlin).
- **Copernicus Attribution:** Contains modified Copernicus Sentinel data (2017-2018), processed by ESA and TU Berlin.

---

## 3. Evaluation Benchmarks: VRSBench & RSVQA

### 3.1 Strict Quarantine Discipline
To uphold empirical scientific integrity, **zero training was performed on evaluation benchmarks**. 
- All evaluation splits are physically and programmatically quarantined in `evaluation/vrsbench/` and `evaluation/rsvqa/`.
- No weight updates or hyperparameter selections utilized benchmark annotations.

### 3.2 Benchmark Comparison Table

| Benchmark | Primary Task | Annotation Type | Spatial Resolution | Modality | Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **VRSBench** | RS VQA & Grounding | Detailed captions, question-answer pairs, visual bounding boxes | High-resolution (0.5m - 2.0m) | RGB Optical | Li et al. (2024), *VRSBench: A Versatile Vision-Language Benchmark for Remote Sensing* |
| **RSVQA** | Low/High-Res RS VQA | Presence, count, comparison questions | 10m (Sentinel-2) / 0.15m (Aerial) | Optical | Lobry et al. (2020), *RSVQA: Visual Question Answering for Remote Sensing Data* |

---

## 4. Verification & Integrity Hashes
The raw dataset manifests, splits, and trained weights are hashed using SHA-256:

| Artifact | File Path | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| **Dataset Manifest** | `data/manifests/bigearthnet_manifest.json` | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` | Verified |
| **Train Split** | `data/splits/train.json` | `7d10e8d01d4a896d8ddb54e7d488e0b686b245df6a908a8a4760bc0c5717616f` | Verified |
| **Validation Split** | `data/splits/validation.json` | `e2a472c67cfd85e786b45a0b73c9886a117cb34d40d9980d23ddcd98c2538965` | Verified |
| **Test Split** | `data/splits/test.json` | `f3c3a9d316499872be97e9e7f84964e5264b383ae89994c63aa0ec028a2a884d` | Verified |
| **LoRA Adapter Weights** | `artifacts/models/satquery-rs-adapter/adapter/adapter_model.bin` | `b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9` | Verified |
