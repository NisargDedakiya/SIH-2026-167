# Phase 7: Dataset Strategy & Multi-Dataset Protocol

## 1. Multi-Dataset Philosophy
SatQuery AI does NOT treat remote-sensing datasets as interchangeable blobs. Each dataset serves a distinct, architecturally grounded role in the adaptation and evaluation pipeline:

| Dataset | Modality | Primary Purpose | Role in SatQuery |
|---|---|---|---|
| **BigEarthNet v2.0** | Optical (Sentinel-2 12-band) + SAR (Sentinel-1 VV/VH) | Land-cover semantics & EO representation | Primary training & adaptation source |
| **VRSBench** | High-resolution Optical | Vision-Language Grounding & Detailed QA | Evaluation benchmark & instruction tuning |
| **RSVQA** | Low/High-Res Optical | Quantitative counting & presence QA | Strict zero-shot evaluation benchmark |
| **CDVQA** | Bi-Temporal Optical Pairs | Temporal Change Visual Question Answering | Change detection evaluation |

---

## 2. Strict Data Segregation Invariant
1. **Never Train on Benchmark Test Splits**:
   - VRSBench test split and RSVQA test split are strictly quarantined for evaluation.
   - Any model checkpoint found to have trained on benchmark test samples is automatically flagged as invalid.
2. **Deterministic Partitioning**:
   - All dataset splits are generated using fixed seeds (default seed: `42`).
   - Where geographic metadata is available (e.g. tile IDs or coordinate clusters), grouping is enforced to prevent spatial auto-correlation leakage between training and validation sets.
3. **Data Provenance Manifests**:
   - Every training run links directly to a cryptographically hashed dataset manifest (`dataset_manifest.json`), recording sample counts, class distributions, and preprocessing versions.
