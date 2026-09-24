"""
VRSBench Benchmark Dataset Adapter for SatQuery AI.
Supports VQA, Captioning, and Visual Grounding tasks.
Ref: VRSBench: A Versatile Remote Sensing Benchmark.
"""

from typing import Any, Dict, Iterator, List, Optional
import numpy as np
from PIL import Image

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample


class VRSBenchAdapter(BenchmarkDataset):
    """
    Adapter for VRSBench remote-sensing benchmark.
    """

    name = "VRSBench"
    version = "1.0.0"
    supported_tasks = ["VQA", "CAPTIONING", "GROUNDING"]

    VRSBENCH_EVAL_ITEMS = [
        {
            "id": "vrsbench_eval_01",
            "category": "rural_vegetation",
            "query": "What type of agricultural land is present in this remote sensing scene?",
            "reference_answer": "Arable land and complex cultivation patterns.",
            "reference_caption": "A high-resolution aerial view showing arable farmland, pastures, and complex agricultural cultivation parcels.",
            "reference_regions": [
                {"label": "arable land", "box_2d": [10, 15, 90, 85]}
            ],
            "dominant_color": [140, 130, 70],
        },
        {
            "id": "vrsbench_eval_02",
            "category": "water_inundation",
            "query": "Is there a permanent water body visible in this satellite patch?",
            "reference_answer": "Yes, water bodies and inland wetlands are present.",
            "reference_caption": "Satellite optical observation displaying a clear inland water body with dark near-infrared absorption signatures.",
            "reference_regions": [
                {"label": "water body", "box_2d": [20, 25, 95, 90]}
            ],
            "dominant_color": [25, 60, 110],
        },
        {
            "id": "vrsbench_eval_03",
            "category": "urban_infrastructure",
            "query": "What built infrastructure dominates this remote sensing image?",
            "reference_answer": "Urban fabric and industrial or commercial units.",
            "reference_caption": "Dense urban fabric comprising commercial structures, regular road networks, and engineered residential roofs.",
            "reference_regions": [
                {"label": "urban fabric", "box_2d": [15, 10, 85, 95]}
            ],
            "dominant_color": [130, 135, 140],
        },
        {
            "id": "vrsbench_eval_04",
            "category": "forest_canopy",
            "query": "Describe the vegetative cover in this mountainous area.",
            "reference_answer": "Broad-leaved forest and mixed forest canopy.",
            "reference_caption": "A dense woodland canopy consisting of broad-leaved and coniferous forest with active vegetative vigor.",
            "reference_regions": [
                {"label": "forest canopy", "box_2d": [5, 5, 95, 95]}
            ],
            "dominant_color": [30, 95, 40],
        },
        {
            "id": "vrsbench_eval_05",
            "category": "coastal_features",
            "query": "What coastal land cover features are present?",
            "reference_answer": "Beaches, dunes, sands and coastal wetlands.",
            "reference_caption": "A coastal interface featuring sandy beaches, marine dunes, and shallow transitional coastal wetlands.",
            "reference_regions": [
                {"label": "beach dunes", "box_2d": [30, 10, 80, 75]}
            ],
            "dominant_color": [180, 170, 120],
        },
    ]

    def __init__(self, target_task: str = "VQA", data_dir: Optional[Path] = None, allow_synthetic_fixtures: bool = False):
        self.target_task = target_task.upper()
        self.data_dir = data_dir or Path("data/benchmarks/vrsbench")
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
                self.availability_reason = f"Error reading VRSBench annotations: {e}"
                return

        # Real dataset is not present on disk
        if self.allow_synthetic_fixtures:
            self.is_available = True
            self.availability_reason = "RUNNING_SYNTHETIC_SMOKE_TEST_FIXTURE (Not real benchmark data)"
            self._is_loaded = True
        else:
            self.is_available = False
            self.availability_reason = (
                f"Dataset files not found at '{real_path}'. "
                f"Real VRSBench benchmark evaluation requires acquiring the official dataset "
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
                img_path = Path(item["image_path"])
                if not img_path.exists():
                    continue
                img = Image.open(img_path).convert("RGB")
                yield BenchmarkSample(
                    sample_id=item["id"],
                    task=self.target_task,
                    inputs={"image": img, "optical": img},
                    query=item.get("query", "Describe this remote sensing scene."),
                    reference=item.get("reference", {}),
                    metadata={"benchmark": "VRSBench", "is_synthetic": False},
                )
                count += 1
            return

        # Synthetic fixture mode (strictly for code sanity checking, never claimed as real benchmark)
        if self.allow_synthetic_fixtures:
            count = 0
            for item in self.VRSBENCH_EVAL_ITEMS:
                if limit and count >= limit:
                    break

                h, w = (128, 128)
                arr = np.zeros((h, w, 3), dtype=np.uint8)
                arr[:, :] = item["dominant_color"]
                np.random.seed(abs(hash(item["id"])) % (2**32))
                noise = np.random.normal(0, 8, (h, w, 3)).astype(np.int16)
                arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr)

                query = item["query"]
                if self.target_task == "CAPTIONING":
                    query = "Generate a comprehensive descriptive caption for this remote sensing scene."
                elif self.target_task == "GROUNDING":
                    query = f"Detect and localize {item['reference_regions'][0]['label']} in this image."

                yield BenchmarkSample(
                    sample_id=item["id"],
                    task=self.target_task,
                    inputs={"image": img, "optical": img},
                    query=query,
                    reference={
                        "answer": item["reference_answer"],
                        "caption": item["reference_caption"],
                        "regions": item["reference_regions"],
                        "category": item["category"],
                    },
                    metadata={"category": item["category"], "benchmark": "VRSBench", "is_synthetic": True},
                )
                count += 1

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "tasks": self.supported_tasks,
            "sample_count": len(self.VRSBENCH_EVAL_ITEMS),
            "split": self.split,
            "spatial_resolution": "High-resolution nadir optical imagery",
        }

    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        return sample.reference
