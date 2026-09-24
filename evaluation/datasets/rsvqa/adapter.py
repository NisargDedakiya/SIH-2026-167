"""
RSVQA Benchmark Dataset Adapter for SatQuery AI.
Supports presence, comparison, and counting remote-sensing queries.
Ref: RSVQA: Visual Question Answering for Remote Sensing Data.
"""

from typing import Any, Dict, Iterator, List, Optional
import numpy as np
from PIL import Image

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample


class RSVQAAdapter(BenchmarkDataset):
    """
    Adapter for RSVQA benchmark evaluation.
    """

    name = "RSVQA"
    version = "1.0.0"
    supported_tasks = ["VQA", "visual_question_answering"]

    RSVQA_SAMPLES = [
        {
            "id": "rsvqa_presence_01",
            "type": "presence",
            "query": "Is there a water body present in this satellite scene?",
            "reference": "yes",
            "dominant_color": [30, 65, 120],
        },
        {
            "id": "rsvqa_presence_02",
            "type": "presence",
            "query": "Are there buildings or built-up infrastructure present in this area?",
            "reference": "no",
            "dominant_color": [35, 100, 45],
        },
        {
            "id": "rsvqa_comparison_01",
            "type": "comparison",
            "query": "Is the area mostly urban or rural agricultural land?",
            "reference": "rural agricultural land",
            "dominant_color": [140, 130, 70],
        },
        {
            "id": "rsvqa_presence_03",
            "type": "presence",
            "query": "Does this scene contain residential urban fabric?",
            "reference": "yes",
            "dominant_color": [135, 135, 140],
        },
        {
            "id": "rsvqa_comparison_02",
            "type": "comparison",
            "query": "Is the land cover primarily forest or water body?",
            "reference": "forest",
            "dominant_color": [28, 90, 38],
        },
        {
            "id": "rsvqa_count_01",
            "type": "counting",
            "query": "Are there multiple distinct agricultural parcels visible?",
            "reference": "yes",
            "dominant_color": [130, 120, 65],
        },
    ]

    def __init__(self, data_dir: Optional[Path] = None, allow_synthetic_fixtures: bool = False):
        self.data_dir = data_dir or Path("data/benchmarks/rsvqa")
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
                self.availability_reason = f"Error reading RSVQA annotations: {e}"
                return

        if self.allow_synthetic_fixtures:
            self.is_available = True
            self.availability_reason = "RUNNING_SYNTHETIC_SMOKE_TEST_FIXTURE (Not real benchmark data)"
            self._is_loaded = True
        else:
            self.is_available = False
            self.availability_reason = (
                f"Dataset files not found at '{real_path}'. "
                f"Real RSVQA benchmark evaluation requires acquiring the official dataset "
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
                    task="VQA",
                    inputs={"image": img, "optical": img},
                    query=item["query"],
                    reference={"answer": item["reference"], "question_type": item.get("type", "general")},
                    metadata={"question_type": item.get("type", "general"), "benchmark": "RSVQA", "is_synthetic": False},
                )
                count += 1
            return

        if self.allow_synthetic_fixtures:
            count = 0
            for item in self.RSVQA_SAMPLES:
                if limit and count >= limit:
                    break

                h, w = (128, 128)
                arr = np.zeros((h, w, 3), dtype=np.uint8)
                arr[:, :] = item["dominant_color"]
                np.random.seed(abs(hash(item["id"])) % (2**32))
                noise = np.random.normal(0, 8, (h, w, 3)).astype(np.int16)
                arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr)

                yield BenchmarkSample(
                    sample_id=item["id"],
                    task="VQA",
                    inputs={"image": img, "optical": img},
                    query=item["query"],
                    reference={"answer": item["reference"], "question_type": item["type"]},
                    metadata={"question_type": item["type"], "benchmark": "RSVQA", "is_synthetic": True},
                )
                count += 1

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "tasks": self.supported_tasks,
            "sample_count": len(self.RSVQA_SAMPLES),
            "split": self.split,
            "question_types": ["presence", "comparison", "counting"],
        }

    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        return sample.reference
