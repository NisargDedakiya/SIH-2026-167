"""
Bi-Temporal Pair Validator.
Validates temporal ordering (T1 < T2), acquisition timestamps, and spatial compatibility.
"""

import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.database.models import ImageModel
from app.temporal.compatibility import SpatialCompatibilityChecker
from app.temporal.schemas import PairValidationResult


class BiTemporalValidator:
    """
    Validates that a pair of satellite images forms a legally valid bi-temporal baseline.
    """

    @classmethod
    def validate_pair(
        cls,
        image_t1: ImageModel,
        image_t2: ImageModel,
        override_t1_time: Optional[datetime.datetime] = None,
        override_t2_time: Optional[datetime.datetime] = None,
        min_overlap: Optional[float] = None
    ) -> PairValidationResult:
        """
        Runs comprehensive validation across temporal ordering and spatial compatibility.
        """
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Image Identity Check
        if str(image_t1.id) == str(image_t2.id):
            errors.append("T1 and T2 reference the exact same image ID. Two distinct acquisitions are required.")
            return PairValidationResult(
                valid=False,
                temporal_valid=False,
                spatially_compatible=True,
                overlap_ratio=1.0,
                status_code="IDENTICAL_IMAGES",
                message="Cannot perform bi-temporal change analysis on identical image instances.",
                warnings=warnings,
                errors=errors,
            )

        # 2. Temporal Validation
        t1_time = override_t1_time or image_t1.acquisition_time
        t2_time = override_t2_time or image_t2.acquisition_time

        temporal_valid = True

        if not t1_time or not t2_time:
            temporal_valid = False
            warnings.append(
                "Acquisition timestamp missing for one or both images. Temporal ordering (T1 < T2) assumed based on selection order."
            )
        else:
            if t1_time > t2_time:
                temporal_valid = False
                errors.append(
                    f"Invalid temporal order: T1 ({t1_time.isoformat()}) is later than T2 ({t2_time.isoformat()}). T1 must be the earlier baseline image."
                )
            elif t1_time == t2_time:
                temporal_valid = False
                errors.append(
                    f"Equal acquisition timestamps ({t1_time.isoformat()}). Bi-temporal change analysis requires different observation times."
                )

        # 3. Spatial Compatibility Validation
        spatial_result = SpatialCompatibilityChecker.check_spatial_compatibility(
            image_t1=image_t1,
            image_t2=image_t2,
            min_overlap=min_overlap
        )

        spatially_compatible = spatial_result["compatible"]
        overlap_ratio = spatial_result["overlap_ratio"]

        if not spatially_compatible:
            errors.append(spatial_result["message"])
        elif spatial_result.get("needs_reprojection"):
            warnings.append(f"CRS mismatch ({image_t1.crs} vs {image_t2.crs}). Co-registration reprojection will be applied.")
        elif spatial_result.get("needs_resampling"):
            warnings.append("Resolution or dimension difference detected. Resampling will be applied during alignment.")

        # Determine overall validity
        overall_valid = len(errors) == 0

        status_code = "VALID"
        if not overall_valid:
            if any("temporal" in e.lower() for e in errors):
                status_code = "INVALID_TEMPORAL_ORDER"
            elif any("spatial" in e.lower() or "overlap" in e.lower() for e in errors):
                status_code = "NO_SPATIAL_OVERLAP"
            else:
                status_code = "VALIDATION_FAILED"

        message = "Bi-temporal pair is valid and ready for change analysis."
        if not overall_valid:
            message = "; ".join(errors)
        elif warnings:
            message = f"Pair valid with considerations: {'; '.join(warnings)}"

        return PairValidationResult(
            valid=overall_valid,
            temporal_valid=temporal_valid,
            spatially_compatible=spatially_compatible,
            overlap_ratio=overlap_ratio,
            status_code=status_code,
            message=message,
            warnings=warnings,
            errors=errors,
        )
