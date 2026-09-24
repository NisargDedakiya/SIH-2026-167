"""
ISRO/SAC Evaluation Adapter for SatQuery AI (Part 10 & Part 51).
Supports pre-georeferenced/co-registered Cartosat-2S optical and RISAT SAR pairs.
Truthfully checks local storage without fabricating access.
"""

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from PIL import Image

from evaluation.core.dataset import BenchmarkDataset
from evaluation.core.sample import BenchmarkSample


class ISROSACAdapter(BenchmarkDataset):
    """
    Adapter for ISRO Space Applications Centre (SAC) benchmark data:
    Co-registered Cartosat-2S (0.65m sub-meter optical) and RISAT (C-band SAR).
    """

    name = "ISRO_SAC"
    version = "1.0.0"
    supported_tasks = ["CROSS_MODAL", "cross_modal_analysis"]

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/raw/isro_sac")
        self.samples: List[Dict[str, Any]] = []
        self._is_loaded = False
        self.split = "test"
        self._check_availability()

    def _check_availability(self) -> None:
        """Verifies actual existence of ISRO/SAC dataset files on disk."""
        target_dir = self.data_dir
        if not target_dir.is_absolute():
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            target_dir = root_dir / self.data_dir

        if target_dir.exists() and any(target_dir.glob("*.tif")):
            self.is_available = True
            self.availability_reason = "Dataset present on disk."
        else:
            self.is_available = False
            self.availability_reason = (
                f"ISRO/SAC Cartosat-2S / RISAT evaluation archive not found at '{target_dir}'. "
                f"Status: NOT RUN (Dataset requires authorized local download)."
            )

    def load(self, split: str = "test") -> None:
        self.split = split
        self._check_availability()
        if not self.is_available:
            return
        self._is_loaded = True

    def iter_samples(self, limit: Optional[int] = None) -> Iterator[BenchmarkSample]:
        if not self.is_available:
            return
        # If files exist, yield samples
        count = 0
        for opt_file in self.data_dir.glob("*_optical.tif"):
            if limit and count >= limit:
                break
            sar_file = self.data_dir / opt_file.name.replace("_optical.tif", "_sar.tif")
            if sar_file.exists():
                sample = BenchmarkSample(
                    sample_id=opt_file.stem,
                    task="CROSS_MODAL",
                    inputs={
                        "optical_path": str(opt_file),
                        "sar_path": str(sar_file),
                        "optical": Image.open(opt_file).convert("RGB"),
                        "sar": Image.open(sar_file).convert("RGB"),
                    },
                    query="Perform cross-modal optical and SAR feature verification.",
                    reference={"modality": "optical_sar", "verified": True},
                    metadata={"sensor_optical": "Cartosat-2S", "sensor_sar": "RISAT-1/1A"},
                )
                yield sample
                count += 1

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "sensors": ["Cartosat-2S (PAN/VNIR 0.65m)", "RISAT-1/1A (C-band SAR)"],
            "source": "ISRO Space Applications Centre (SAC)",
            "is_available": self.is_available,
            "availability_reason": self.availability_reason,
            "tasks": self.supported_tasks,
        }

    def get_reference(self, sample: BenchmarkSample) -> Dict[str, Any]:
        return sample.reference
