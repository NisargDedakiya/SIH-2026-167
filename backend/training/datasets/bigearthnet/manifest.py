"""
BigEarthNet Dataset Manifest Generator and Serializer.
Produces machine-readable JSON manifests recording provenance, sample records, and class distributions.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class BigEarthNetManifestGenerator:
    """
    Generates structured, reproducible manifests for BigEarthNet datasets.
    """

    @staticmethod
    def compute_sha256(data_bytes: bytes) -> str:
        return hashlib.sha256(data_bytes).hexdigest()

    @classmethod
    def generate_manifest(
        cls,
        dataset_name: str,
        version: str,
        samples: List[Dict[str, Any]],
        split_ratios: Optional[Dict[str, float]] = None,
        source_url: str = "https://bigearth.net",
        license_name: str = "Community Data License Agreement (CDLA-Permissive-1.0)",
    ) -> Dict[str, Any]:
        """
        Creates a structured dataset manifest dictionary.
        """
        class_histogram: Dict[str, int] = {}
        total_optical = 0
        total_sar = 0

        clean_samples: List[Dict[str, Any]] = []
        for s in samples:
            labels = s.get("labels", [])
            for lbl in labels:
                class_histogram[lbl] = class_histogram.get(lbl, 0) + 1

            if s.get("optical_path"):
                total_optical += 1
            if s.get("sar_path"):
                total_sar += 1

            clean_samples.append({
                "sample_id": s["sample_id"],
                "optical_path": s.get("optical_path"),
                "sar_path": s.get("sar_path"),
                "labels": labels,
                "metadata": s.get("metadata", {}),
            })

        content_str = json.dumps(clean_samples, sort_keys=True)
        manifest_hash = cls.compute_sha256(content_str.encode("utf-8"))

        manifest = {
            "dataset_name": dataset_name,
            "version": version,
            "source_url": source_url,
            "license": license_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "manifest_hash": manifest_hash,
            "total_samples": len(clean_samples),
            "modalities": {
                "optical_count": total_optical,
                "sar_count": total_sar,
                "paired_count": sum(1 for s in clean_samples if s.get("optical_path") and s.get("sar_path")),
            },
            "split_ratios": split_ratios or {"train": 0.70, "val": 0.15, "test": 0.15},
            "class_distribution": class_histogram,
            "samples": clean_samples,
        }
        return manifest

    @classmethod
    def save_manifest(cls, manifest: Dict[str, Any], output_path: str | Path) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return out

    @classmethod
    def load_manifest(cls, manifest_path: str | Path) -> Dict[str, Any]:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
