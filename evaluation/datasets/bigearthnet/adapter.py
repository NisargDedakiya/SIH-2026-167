"""
BigEarthNet v2.0 Benchmark Dataset Adapter for SatQuery AI.
Reuses Phase 7 validated partitions and strictly evaluates on the isolated test split.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from PIL import Image

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample


class BigEarthNetBenchmarkAdapter(BenchmarkDataset):
    """
    Adapter for BigEarthNet v2.0 benchmark evaluation.
    Evaluates multi-label land cover recognition and remote-sensing VQA.
    """

    name = "BigEarthNet"
    version = "2.0.0"
    supported_tasks = ["VQA", "visual_question_answering"]

    def __init__(self, splits_dir: Optional[Path] = None):
        self.splits_dir = splits_dir or Path("data/splits")
        self.samples: List[Dict[str, Any]] = []
        self._is_loaded = False
        self.split = "test"

    def load(self, split: str = "test") -> None:
        self.split = split
        split_file = self.splits_dir / f"{split}.json"
        if not split_file.exists():
            # Try finding relative to workspace root
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            split_file = root_dir / "data" / "splits" / f"{split}.json"

        if not split_file.exists():
            self.is_available = False
            self.availability_reason = f"Split file '{split_file}' not found."
            return

        with open(split_file, "r", encoding="utf-8") as f:
            self.samples = json.load(f)

        self.is_available = True
        self._is_loaded = True

    def iter_samples(self, limit: Optional[int] = None) -> Iterator[BenchmarkSample]:
        if not self._is_loaded:
            self.load(self.split)

        count = 0
        for item in self.samples:
            if limit and count >= limit:
                break

            opt_path = Path(item["optical_path"])
            sar_path = Path(item.get("sar_path", ""))

            # Open image safely
            img = None
            if opt_path.exists():
                img = Image.open(opt_path).convert("RGB")
            else:
                img = Image.new("RGB", (120, 120), color=(80, 120, 60))

            sar_img = None
            if sar_path.exists():
                sar_img = Image.open(sar_path).convert("RGB")

            labels = item.get("labels", [])
            ref_str = ", ".join(labels) if labels else "Unknown land cover"

            sample = BenchmarkSample(
                sample_id=item["sample_id"],
                task="VQA",
                inputs={
                    "image": img,
                    "optical": img,
                    "sar": sar_img,
                    "optical_path": str(opt_path),
                    "sar_path": str(sar_path) if sar_path else None,
                },
                query="What is the dominant land cover class in this satellite patch?",
                reference={
                    "answer": ref_str,
                    "labels": labels,
                },
                metadata=item.get("metadata", {}),
            )

            yield sample
            count += 1

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "sensors": ["Sentinel-2 MSI (12 bands)", "Sentinel-1 SAR (VV, VH)"],
            "resolution_m": 10.0,
            "classes": 19,
            "taxonomy": "CORINE Land Cover (CLC)",
            "split": self.split,
        }

    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        return sample.reference
