# Benchmark Dataset Acquisition Guide

**SatQuery AI — Scientific Validation & Benchmark Ingestion (Phase 11A)**

This document details the acquisition protocols, expected local filesystem layout, and ingestion pipelines for genuine remote-sensing benchmarks.

---

## 1. Directory Structure Contract

All benchmark adapters expect datasets to reside under `data/benchmarks/`:

```
data/
├── benchmarks/
│   ├── vrsbench/
│   │   ├── test_annotations.json
│   │   └── images/
│   │       ├── 00001.png
│   │       └── ...
│   ├── rsvqa/
│   │   ├── test_annotations.json
│   │   └── images/
│   ├── cdvqa/
│   │   ├── test_annotations.json
│   │   ├── t1_images/
│   │   └── t2_images/
│   └── bigearthnet/
│       ├── BigEarthNet-v1.0/
│       └── splits/
```

If a benchmark directory is absent on disk, the SatQuery evaluation runner strictly marks the dataset as **`NOT RUN`**. It will **never** generate fake synthetic data or fabricate benchmark metrics.

---

## 2. Dataset Acquisition Details

### 2.1 VRSBench (Versatile Remote Sensing Benchmark)
* **Tasks:** Visual Question Answering, Scene Captioning, Visual Grounding
* **Source:** [VRSBench Official Repository / Hugging Face](https://huggingface.co/datasets/VRSBench)
* **Format:** Optical high-resolution aerial imagery with polygon & bounding box annotations.
* **Setup:**
  ```bash
  mkdir -p data/benchmarks/vrsbench/images
  # Download test split annotations:
  # Place annotations at data/benchmarks/vrsbench/test_annotations.json
  ```

### 2.2 RSVQA (Remote Sensing Visual Question Answering)
* **Tasks:** Presence, Comparison, and Counting VQA
* **Source:** [RSVQA Project (Sylvain Lobry et al.)](https://rsvqa.sylvainlobry.com/)
* **Format:** Sentinel-2 and high-resolution urban patches with question-answer pairs.
* **Setup:**
  ```bash
  mkdir -p data/benchmarks/rsvqa/images
  # Place test annotations at data/benchmarks/rsvqa/test_annotations.json
  ```

### 2.3 CDVQA (Change Detection Visual Question Answering)
* **Tasks:** Bi-Temporal reasoning across $T_1$ and $T_2$ acquisitions
* **Source:** [CDVQA Benchmark Repository](https://github.com/Chen-H-H/CDVQA)
* **Format:** Dual-temporal registered satellite tiles with change queries.
* **Setup:**
  ```bash
  mkdir -p data/benchmarks/cdvqa/t1_images data/benchmarks/cdvqa/t2_images
  # Place test annotations at data/benchmarks/cdvqa/test_annotations.json
  ```

### 2.4 BigEarthNet v2.0 (Multimodal Sentinel-1 & Sentinel-2)
* **Tasks:** Land-cover classification, multi-label recognition, cross-modal alignment
* **Source:** [BigEarthNet Official Archive](https://bigearth.net/)
* **Format:** 590,326 pairs of Sentinel-2 multispectral and Sentinel-1 dual-polarization SAR patches.
* **Setup:**
  ```bash
  # For full training:
  python scripts/setup_bigearthnet.py --source /path/to/BigEarthNet-v2.0
  ```

---

## 3. Running Real Benchmark Evaluations

Once datasets are in place:

```bash
# Evaluate genuine VRSBench VQA:
python -m evaluation.run --dataset vrsbench --task vqa --model satquery-rs-v1

# Evaluate genuine RSVQA:
python -m evaluation.run --dataset rsvqa --task vqa --model satquery-rs-v1

# Evaluate bi-temporal CDVQA:
python -m evaluation.run --dataset cdvqa --task change_vqa --model remote-sensing-change
```

All evaluations measure and report actual wall-clock elapsed time in milliseconds.
