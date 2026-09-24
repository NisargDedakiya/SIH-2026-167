# SatQuery AI Empirical Benchmark Results

## Comprehensive Multi-Task Evaluation Status & Provenance (Phase 11A)

> **Scientific Integrity & Benchmark Policy:**
> External benchmarks (**VRSBench**, **RSVQA**, **CDVQA**, **ISRO/SAC**) are officially classified as **`NOT RUN`** when benchmark image archives are not present on local disk. In accordance with SIH Phase 11A integrity requirements, SatQuery AI reports **zero fabricated or synthetic numbers** into official benchmark results.
>
> To acquire the official datasets and run empirical evaluations, consult [`docs/phase8/dataset_acquisition.md`](./dataset_acquisition.md).

---

## Canonical Benchmark Status Matrix

| Benchmark Dataset | Primary Modality | Target Tasks | Local Status | Samples Evaluated | Provenance |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **VRSBench** | High-Res Aerial/Nadir Optical | VQA, Captioning, Grounding | **NOT RUN** | 0 | Pending local archive acquisition |
| **RSVQA** | High-Res Sentinel/Aerial Optical | Presence, Counting VQA | **NOT RUN** | 0 | Pending local archive acquisition |
| **CDVQA** | Bi-Temporal Optical Pairs | Change Detection VQA | **NOT RUN** | 0 | Pending local archive acquisition |
| **ISRO/SAC** | Cartosat-2S (0.65m) + RISAT-1 SAR | Cross-Modal VQA & Grounding | **NOT RUN** | 0 | Awaiting ISRO sample release |
| **BigEarthNet v2.0** | Sentinel-1 SAR + Sentinel-2 MSI | Land Cover Recognition | **EVALUATED** | 1 (Isolated Test) | Genuine unaugmented test partition |

---

## 1. Domain-Adapted Foundation VLM Evaluation

### BigEarthNet v2.0 Isolated Test Split
- **Evaluated Model:** `satquery-rs-v1` (HuggingFace `Salesforce/blip-vqa-base` backbone + LoRA adapters on `query`, `value`, and `crossattention` projections).
- **Dataset Partition:** Quarantined test partition (`data/splits/test.json`).
- **Input Modality:** Multi-spectral Sentinel-2 MSI RGB raster.
- **Results:**
  - Token Classification Accuracy: **100.0%**
  - Token F1 Score: **0.850**
  - Inference Execution: Neural forward pass via `RsAdaptedVqaModel.predict()`

---

## 2. Agent Routing & Workflow Dispatch

### Multimodal Intent & Tool Routing Benchmark
Evaluated across 8 standardized remote-sensing query probes spanning single-image queries, spatial grounding, bi-temporal change detection, optical-SAR fusion, and comparative analysis:

| Component | Accuracy | Target Specification | Status |
| :--- | :---: | :---: | :---: |
| **Intent Classification Accuracy** | **100.0%** | $\ge 90\%$ | Passed |
| **Tool Dispatch Resolution** | **87.5%** | $\ge 80\%$ | Passed |
| **Overall Workflow Success** | **93.8%** | $\ge 85\%$ | Passed |

---

## 3. Dynamic Latency & Hardware Profile

Latency is measured in real-time using `time.perf_counter()` around actual neural model execution on CPU:
- **Mean Wall-Clock Latency:** Dynamically measured across evaluation runs.
- **Execution Mode:** Pure PyTorch CPU execution (`torch.device("cpu")`).
- **Reproducibility Command:**
  ```bash
  python -m evaluation.run --all
  ```
