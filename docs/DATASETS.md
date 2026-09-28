# SatQuery AI — Dataset Integrations & Benchmark Specifications

**Project:** SatQuery AI  
**Scope:** Dataset Adapters, Synthetic Sample Generators, and Benchmark Partitions  
**Evaluation Standard:** Zero Fabrication Policy (No synthetic numbers claimed as real benchmark scores)  

---

## 1. Overview of Supported Datasets

SatQuery AI interfaces with five benchmark datasets spanning multi-spectral optical, synthetic aperture radar (SAR), bi-temporal change pairs, and Indian satellite missions:

| Dataset | Modality & Sensors | Primary Tasks | Repository Adapter | Local Data Status | License / Terms |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **BigEarthNet v2.0** | Multi-Spectral (Sentinel-2) + C-Band SAR (Sentinel-1) | Domain Adaptation, Multi-Label Land Cover VQA | `evaluation/datasets/bigearthnet/` | ✅ Evaluated on sample partition | CDLA-Permissive-1.0 |
| **VRSBench** | High-Resolution Optical Imagery (0.5m – 2m) | Remote-Sensing VQA, Dense Captioning, Visual Grounding | `evaluation/datasets/vrsbench/adapter.py` | 🟡 Configured (Requires external download) | Research Use |
| **RSVQA** | Low-Res (Sentinel-2) & High-Res (Aerial) Optical | Object Presence, Counting, Land Cover Classification | `evaluation/datasets/rsvqa/adapter.py` | 🟡 Configured (Requires external download) | Research / CC-BY-4.0 |
| **CDVQA** | Bi-Temporal Optical Satellite Pairs | Change Detection VQA, Temporal Differencing | `evaluation/datasets/cdvqa/adapter.py` | 🟡 Configured (Requires external download) | Research Use |
| **ISRO / SAC** | Cartosat-2S (0.65m Optical), RISAT-1A (C-band SAR) | High-Resolution Cross-Modal Fusion, Indian Land Cover | `evaluation/datasets/isro_sac/adapter.py` | 🟡 Configured (Requires authorized data) | ISRO Open Data / SAC Terms |

---

## 2. BigEarthNet v2.0 Integration & Preprocessing

BigEarthNet v2.0 is the primary dataset used for training the domain-adapted model (`satquery-rs-v1`):
- **Structure:** Co-registered Sentinel-2 (12 spectral bands) and Sentinel-1 (VV, VH dual-polarization SAR) patches.
- **Taxonomy:** 19 CORINE Land Cover (CLC) classes (e.g., *Discontinuous urban fabric*, *Non-irrigated arable land*, *Coniferous forest*, *Water bodies*).
- **Synthetic Sample Generator:** `scripts/generate_bigearthnet_samples.py` generates verifiable multi-spectral GeoTIFF patches for pipeline testing without downloading 100GB+ archives.
- **Loader:** `training/datasets/bigearthnet/loader.py` and `backend/training/datasets/bigearthnet/loader.py` provide deterministic train/val/test splits preventing data leakage.

---

## 3. Benchmark Dataset Adapters

Every dataset adapter implements the unified `BenchmarkAdapter` interface (`evaluation/core/dataset.py`):
```python
class BenchmarkAdapter(ABC):
    @abstractmethod
    def load_samples(self, split: str = "test", limit: Optional[int] = None) -> List[BenchmarkSample]:
        raise NotImplementedError

    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        raise NotImplementedError
```

### Unified `BenchmarkSample` Structure:
```python
@dataclass
class BenchmarkSample:
    sample_id: str
    dataset_name: str
    task: str  # "VQA", "CAPTIONING", "GROUNDING", "CHANGE"
    primary_image_path: str
    secondary_image_path: Optional[str] = None
    query: Optional[str] = None
    reference_answer: Optional[str] = None
    reference_boxes: Optional[List[List[float]]] = None
    reference_mask_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 4. Local Dataset Acquisition Guide

To run full external benchmark runs locally, datasets must be placed in `data/benchmarks/`:

### 4.1 VRSBench Setup
1. Download official VRSBench annotations and images from the official repository.
2. Structure directory as:
   ```text
   data/benchmarks/vrsbench/
   ├── images/
   ├── annotations/
   │   ├── vrsbench_vqa_test.json
   │   ├── vrsbench_caption_test.json
   │   └── vrsbench_grounding_test.json
   ```
3. Run evaluation:
   ```bash
   python -m evaluation.run --dataset vrsbench --task vqa --model satquery-rs-v1
   ```

### 4.2 RSVQA Setup
1. Download RSVQA Low-Resolution (LR) or High-Resolution (HR) JSON files and image archives.
2. Structure directory as:
   ```text
   data/benchmarks/rsvqa/
   ├── Images_LR/
   └── LR_questions.json
   ```

### 4.3 CDVQA Setup
1. Download CDVQA bi-temporal pairs and QA pairs.
2. Place in `data/benchmarks/cdvqa/`.

---

## 5. Zero Fabrication Policy on Datasets

When official dataset archives are not mounted on local disk:
- SatQuery AI **refuses** to fabricate or report synthetic scores.
- `GET /api/v1/evaluation/matrix` honestly reports `status: "NOT RUN"` with explicit explanation: *"Dataset files not found on local disk. Real benchmark evaluation requires acquiring the official dataset per docs/phase8/dataset_acquisition.md. Zero fabricated metrics reported."*
- Evaluation commands without datasets fail closed with clear acquisition instructions rather than emitting mock numbers.
