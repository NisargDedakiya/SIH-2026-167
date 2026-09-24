"""
BigEarthNet Dataset Validator.
Performs strict schema, file existence, band dimension, and label integrity checks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import numpy as np

try:
    from training.datasets.bigearthnet.metadata import (
        BIGEARTHNET_19_CLASSES,
        SENTINEL2_BANDS,
    )
except ImportError:
    from app.training.datasets.bigearthnet.metadata import (
        BIGEARTHNET_19_CLASSES,
        SENTINEL2_BANDS,
    )


@dataclass
class BigEarthNetSampleRecord:
    sample_id: str
    optical_path: Optional[str] = None
    sar_path: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True
    error_reasons: List[str] = field(default_factory=list)


class BigEarthNetValidator:
    """
    Validates BigEarthNet patch samples against rigorous remote-sensing integrity criteria.
    Never silently discards invalid samples; logs and records all reasons.
    """

    def __init__(self, allowed_classes: Optional[List[str]] = None):
        self.allowed_classes: Set[str] = set(allowed_classes or BIGEARTHNET_19_CLASSES)

    def validate_sample(
        self,
        sample_dict: Dict[str, Any],
        check_files_exist: bool = False
    ) -> BigEarthNetSampleRecord:
        """
        Validates a single candidate BigEarthNet record.
        """
        sample_id = sample_dict.get("sample_id", "unknown")
        labels = sample_dict.get("labels", [])
        optical_path = sample_dict.get("optical_path")
        sar_path = sample_dict.get("sar_path")
        meta = sample_dict.get("metadata", {})
        errors: List[str] = []

        # 1. Identifier check
        if not sample_id or sample_id == "unknown":
            errors.append("Missing or invalid sample_id.")

        # 2. Labels validation
        if not labels or not isinstance(labels, list):
            errors.append("Labels list is empty or invalid.")
        else:
            invalid_labels = [l for l in labels if l not in self.allowed_classes]
            if invalid_labels:
                errors.append(f"Unrecognized land cover labels: {invalid_labels}")

        # 3. Path & file existence validation
        if not optical_path and not sar_path:
            errors.append("Neither optical_path nor sar_path provided.")

        if check_files_exist:
            if optical_path and not Path(optical_path).exists():
                errors.append(f"Optical path not found on disk: {optical_path}")
            if sar_path and not Path(sar_path).exists():
                errors.append(f"SAR path not found on disk: {sar_path}")

        # 4. Raster metadata sanity checks (if provided)
        if "dimensions" in meta:
            dims = meta["dimensions"]
            if dims[0] <= 0 or dims[1] <= 0:
                errors.append(f"Invalid raster dimensions: {dims}")

        is_valid = len(errors) == 0
        return BigEarthNetSampleRecord(
            sample_id=sample_id,
            optical_path=optical_path,
            sar_path=sar_path,
            labels=labels,
            metadata=meta,
            is_valid=is_valid,
            error_reasons=errors
        )

    def validate_dataset(
        self,
        samples: List[Dict[str, Any]],
        check_files_exist: bool = False
    ) -> Dict[str, Any]:
        """
        Validates an entire batch/corpus of BigEarthNet records and returns an audit report.
        """
        total = len(samples)
        valid_records: List[BigEarthNetSampleRecord] = []
        invalid_records: List[BigEarthNetSampleRecord] = []
        seen_ids: Set[str] = set()
        duplicate_count = 0

        for s in samples:
            sid = s.get("sample_id")
            if sid in seen_ids:
                duplicate_count += 1
                rec = self.validate_sample(s, check_files_exist=check_files_exist)
                rec.is_valid = False
                rec.error_reasons.append(f"Duplicate sample_id encountered: {sid}")
                invalid_records.append(rec)
                continue

            seen_ids.add(sid)
            rec = self.validate_sample(s, check_files_exist=check_files_exist)
            if rec.is_valid:
                valid_records.append(rec)
            else:
                invalid_records.append(rec)

        report = {
            "total_samples": total,
            "valid_samples": len(valid_records),
            "invalid_samples": len(invalid_records),
            "duplicate_samples": duplicate_count,
            "usable_training": int(len(valid_records) * 0.70),
            "usable_validation": int(len(valid_records) * 0.15),
            "usable_test": len(valid_records) - int(len(valid_records) * 0.70) - int(len(valid_records) * 0.15),
            "error_summary": {},
        }

        # Aggregate error reasons
        for r in invalid_records:
            for err in r.error_reasons:
                report["error_summary"][err] = report["error_summary"].get(err, 0) + 1

        return {
            "report": report,
            "valid_records": valid_records,
            "invalid_records": invalid_records
        }
