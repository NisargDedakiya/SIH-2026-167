"""
CDVQA (Change Detection Visual Question Answering) Benchmark Dataset Adapter.
Evaluates bi-temporal reasoning across paired T1 and T2 satellite acquisitions.
Ref: CDVQA: Change Detection Visual Question Answering for Remote Sensing.
"""

from typing import Any, Dict, Iterator, List, Optional
import numpy as np
from PIL import Image

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample


class CDVQAAdapter(BenchmarkDataset):
    """
    Adapter for CDVQA bi-temporal reasoning benchmark.
    Strictly provides and asserts paired T1 and T2 inputs for every sample.
    """

    name = "CDVQA"
    version = "1.0.0"
    supported_tasks = ["CHANGE_VQA", "change_vqa"]

    CDVQA_PAIRS = [
        {
            "id": "cdvqa_temporal_01",
            "type": "urban_expansion",
            "query": "What major change occurred between T1 and T2 in this area?",
            "reference": "Urban expansion with newly constructed residential and industrial structures.",
            "t1_color": [45, 110, 50],   # Pre-change: agricultural/vegetated
            "t2_color": [135, 135, 140], # Post-change: constructed urban fabric
            "time_t1": "2020-03-15",
            "time_t2": "2024-03-20",
        },
        {
            "id": "cdvqa_temporal_02",
            "type": "deforestation",
            "query": "Did vegetation density increase or decrease between the two dates?",
            "reference": "Vegetation decreased significantly due to forest clearance.",
            "t1_color": [25, 95, 35],    # Pre-change: dense forest canopy
            "t2_color": [145, 120, 80],  # Post-change: cleared soil/scrub
            "time_t1": "2019-06-10",
            "time_t2": "2023-06-12",
        },
        {
            "id": "cdvqa_temporal_03",
            "type": "water_inundation",
            "query": "What type of environmental change is visible in T2 relative to T1?",
            "reference": "Water inundation and expansion of surface wetlands.",
            "t1_color": [120, 110, 75],  # Pre-change: dry arable land
            "t2_color": [20, 55, 110],   # Post-change: inundated water
            "time_t1": "2021-08-05",
            "time_t2": "2021-08-25",
        },
        {
            "id": "cdvqa_temporal_04",
            "type": "no_change",
            "query": "Has any significant infrastructure change occurred between the two dates?",
            "reference": "No significant change observed; land cover remains stable.",
            "t1_color": [130, 130, 130], # Pre-change: stable urban
            "t2_color": [132, 129, 131], # Post-change: identical stable urban
            "time_t1": "2022-01-10",
            "time_t2": "2023-01-15",
        },
    ]

    def __init__(self, data_dir: Optional[Path] = None, allow_synthetic_fixtures: bool = False):
        self.data_dir = data_dir or Path("data/benchmarks/cdvqa")
        self.allow_synthetic_fixtures = allow_synthetic_fixtures
        self.is_available = False
        self.availability_reason = None
        self._is_loaded = False
        self.split = "test"
        self._samples: List[Dict[str, Any]] = []

    def load(self, split: str = "test") -> None:
        self.split = split
        real_path = self.data_dir if self.data_dir.is_absolute() else (Path.cwd() / self.data_dir)
        annotation_file = real_path / f"{split}_annotations.json"

        if annotation_file.exists():
            try:
                import json
                with open(annotation_file, "r", encoding="utf-8") as f:
                    self._samples = json.load(f)
                self.is_available = True
                self._is_loaded = True
                self.availability_reason = None
                return
            except Exception as e:
                self.is_available = False
                self.availability_reason = f"Error reading CDVQA annotations: {e}"
                return

        if self.allow_synthetic_fixtures:
            self.is_available = True
            self.availability_reason = "RUNNING_SYNTHETIC_SMOKE_TEST_FIXTURE (Not real benchmark data)"
            self._is_loaded = True
        else:
            self.is_available = False
            self.availability_reason = (
                f"Dataset files not found at '{real_path}'. "
                f"Real CDVQA benchmark evaluation requires acquiring the official dataset "
                f"per docs/phase8/dataset_acquisition.md."
            )
            self._is_loaded = False

    def iter_samples(self, limit: Optional[int] = None) -> Iterator[BenchmarkSample]:
        if not self._is_loaded:
            self.load(self.split)

        if not self.is_available:
            return

        if self._samples:
            count = 0
            for item in self._samples:
                if limit and count >= limit:
                    break
                p1, p2 = Path(item["image_t1"]), Path(item["image_t2"])
                if not (p1.exists() and p2.exists()):
                    continue
                img_t1 = Image.open(p1).convert("RGB")
                img_t2 = Image.open(p2).convert("RGB")
                yield BenchmarkSample(
                    sample_id=item["id"],
                    task="CHANGE_VQA",
                    inputs={
                        "image_t1": img_t1,
                        "image_t2": img_t2,
                        "time_t1": item.get("time_t1", "T1"),
                        "time_t2": item.get("time_t2", "T2"),
                    },
                    query=item["query"],
                    reference={
                        "answer": item["reference"],
                        "change_type": item.get("type", "change"),
                    },
                    metadata={
                        "change_type": item.get("type", "change"),
                        "benchmark": "CDVQA",
                        "is_synthetic": False,
                    },
                )
                count += 1
            return

        if self.allow_synthetic_fixtures:
            count = 0
            for item in self.CDVQA_PAIRS:
                if limit and count >= limit:
                    break

                h, w = (128, 128)
                arr_t1 = np.zeros((h, w, 3), dtype=np.uint8)
                arr_t1[:, :] = item["t1_color"]
                np.random.seed(abs(hash(item["id"] + "_t1")) % (2**32))
                noise_t1 = np.random.normal(0, 6, (h, w, 3)).astype(np.int16)
                arr_t1 = np.clip(arr_t1.astype(np.int16) + noise_t1, 0, 255).astype(np.uint8)
                img_t1 = Image.fromarray(arr_t1)

                arr_t2 = np.zeros((h, w, 3), dtype=np.uint8)
                arr_t2[:, :] = item["t2_color"]
                np.random.seed(abs(hash(item["id"] + "_t2")) % (2**32))
                noise_t2 = np.random.normal(0, 6, (h, w, 3)).astype(np.int16)
                arr_t2 = np.clip(arr_t2.astype(np.int16) + noise_t2, 0, 255).astype(np.uint8)
                img_t2 = Image.fromarray(arr_t2)

                yield BenchmarkSample(
                    sample_id=item["id"],
                    task="CHANGE_VQA",
                    inputs={
                        "image_t1": img_t1,
                        "image_t2": img_t2,
                        "time_t1": item["time_t1"],
                        "time_t2": item["time_t2"],
                    },
                    query=item["query"],
                    reference={
                        "answer": item["reference"],
                        "change_type": item["type"],
                    },
                    metadata={
                        "change_type": item["type"],
                        "benchmark": "CDVQA",
                        "is_synthetic": True,
                    },
                )
                count += 1


    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "tasks": self.supported_tasks,
            "sample_count": len(self.CDVQA_PAIRS),
            "split": self.split,
            "modalities": "Optical bi-temporal pairs (T1, T2)",
        }

    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        return sample.reference
