"""
Modality Detection and Cross-Modal Pair Validator.
Strictly verifies that an Optical-SAR pair consists of one valid Optical/Multispectral image
and one valid Synthetic Aperture Radar image with verified spatial overlap.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.core.logging import logger
from app.cross_modal.compatibility import CrossModalSpatialCompatibility
from app.cross_modal.models import (
    MODALITY_MULTISPECTRAL,
    MODALITY_OPTICAL,
    MODALITY_SAR,
    MODALITY_UNKNOWN,
    POLARIZATION_DUAL,
    POLARIZATION_HH,
    POLARIZATION_HV,
    POLARIZATION_QUAD,
    POLARIZATION_SINGLE,
    POLARIZATION_UNKNOWN,
    POLARIZATION_VH,
    POLARIZATION_VV,
    SUPPORTED_OPTICAL_MODALITIES,
    SUPPORTED_SAR_MODALITIES,
)
from app.cross_modal.schemas import CrossModalValidationResult
from app.database.models import ImageModel


class CrossModalValidator:
    """
    Validates optical rasters, SAR rasters, and their joint pair compatibility.
    """

    KNOWN_SAR_SENSORS = [
        "risat", "sentinel-1", "s1", "terrasar-x", "alos", "alos-palsar",
        "radarsat", "tandem-x", "cosmo-skymed", "sar", "nisar-sar"
    ]

    KNOWN_OPTICAL_SENSORS = [
        "cartosat", "sentinel-2", "s2", "landsat", "quickbird",
        "worldview", "planetscope", "spot", "pleiades", "optical"
    ]

    @classmethod
    def detect_modality(cls, image: ImageModel, metadata_entries: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Determines whether the image is OPTICAL, MULTISPECTRAL, SAR, or UNKNOWN.
        Evaluates stored modality, sensor names, band configurations, and polarization tags.
        Never silently defaults to optical.
        """
        # 1. Inspect explicit stored modality
        stored_mod = (image.modality or "").lower().strip()
        if stored_mod in ["sar", "synthetic_aperture_radar", "radar"]:
            return MODALITY_SAR
        if stored_mod in ["multispectral", "hyperspectral"]:
            return MODALITY_MULTISPECTRAL
        if stored_mod == "optical":
            return MODALITY_OPTICAL

        # 2. Inspect sensor name
        sensor = (image.sensor or "").lower().strip()
        filename = (image.original_filename or "").lower().strip()

        for sar_name in cls.KNOWN_SAR_SENSORS:
            if sar_name in sensor or sar_name in filename:
                return MODALITY_SAR

        for opt_name in cls.KNOWN_OPTICAL_SENSORS:
            if opt_name in sensor or opt_name in filename:
                return MODALITY_MULTISPECTRAL if image.band_count > 3 else MODALITY_OPTICAL

        # 3. Inspect metadata entries for polarization or SAR tags
        if metadata_entries:
            for entry in metadata_entries:
                data = entry if isinstance(entry, dict) else getattr(entry, "metadata_json", {})
                if not isinstance(data, dict):
                    continue
                # Polarization tags
                if any(k in data for k in ["polarization", "polarisation", "pols", "sar_mode", "radar_band"]):
                    return MODALITY_SAR
                if any(str(v).lower() in ["vv", "vh", "hh", "hv", "dual-pol", "quad-pol"] for v in data.values()):
                    return MODALITY_SAR

        # 4. Inspect filename keywords
        if any(w in filename for w in ["_vv", "_vh", "_hh", "_hv", "grd", "slc", "sar"]):
            return MODALITY_SAR

        if any(w in filename for w in ["rgb", "bgr", "truecolor", "naturalcolor", "visual", "optical"]):
            return MODALITY_OPTICAL

        # 5. Band count heuristics
        if image.band_count in [3, 4] and ("b02" in filename or "b03" in filename or "b04" in filename or "b08" in filename):
            return MODALITY_MULTISPECTRAL

        # If no conclusive evidence is found, declare UNKNOWN
        return MODALITY_UNKNOWN

    @classmethod
    def detect_sar_polarization(cls, image: ImageModel, metadata_entries: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Detects polarization configuration (VV, VH, HH, HV, dual-pol, quad-pol) for SAR data.
        """
        filename = (image.original_filename or "").lower().strip()

        # Check metadata entries
        if metadata_entries:
            for entry in metadata_entries:
                data = entry if isinstance(entry, dict) else getattr(entry, "metadata_json", {})
                if not isinstance(data, dict):
                    continue
                pol = data.get("polarization") or data.get("polarisation")
                if pol:
                    pol_str = str(pol).upper()
                    if pol_str in ["VV", "VH", "HH", "HV"]:
                        return pol_str
                    if "VV" in pol_str and "VH" in pol_str:
                        return POLARIZATION_DUAL
                    if "HH" in pol_str and "HV" in pol_str:
                        return POLARIZATION_DUAL
                    return pol_str

        # Check filename patterns
        if "vv+vh" in filename or "vh+vv" in filename or ("vv" in filename and "vh" in filename):
            return POLARIZATION_DUAL
        if "hh+hv" in filename or "hv+hh" in filename or ("hh" in filename and "hv" in filename):
            return POLARIZATION_DUAL
        if "quad" in filename:
            return POLARIZATION_QUAD
        if "vv" in filename:
            return POLARIZATION_VV
        if "vh" in filename:
            return POLARIZATION_VH
        if "hh" in filename:
            return POLARIZATION_HH
        if "hv" in filename:
            return POLARIZATION_HV

        if image.band_count == 2:
            return POLARIZATION_DUAL
        if image.band_count == 4:
            return POLARIZATION_QUAD
        if image.band_count == 1:
            return POLARIZATION_SINGLE

        return POLARIZATION_UNKNOWN

    @classmethod
    def validate_optical(cls, image: ImageModel) -> Tuple[bool, List[str]]:
        """
        Validates optical/multispectral image technical properties.
        """
        issues = []
        if image.width <= 0 or image.height <= 0:
            issues.append(f"Invalid raster dimensions: {image.width}x{image.height}.")
        if image.band_count < 1:
            issues.append("Optical image has zero available bands.")
        if image.validation_status != "valid":
            issues.append(f"Optical image has invalid validation status: {image.validation_status}.")
        return len(issues) == 0, issues

    @classmethod
    def validate_sar(cls, image: ImageModel) -> Tuple[bool, List[str]]:
        """
        Validates SAR image technical properties.
        """
        issues = []
        if image.width <= 0 or image.height <= 0:
            issues.append(f"Invalid SAR dimensions: {image.width}x{image.height}.")
        if image.band_count < 1:
            issues.append("SAR image has zero available channels.")
        if image.validation_status != "valid":
            issues.append(f"SAR image has invalid validation status: {image.validation_status}.")
        return len(issues) == 0, issues

    @classmethod
    def validate_pair(
        cls,
        optical_image: ImageModel,
        sar_image: ImageModel,
        optical_metadata: Optional[List[Dict[str, Any]]] = None,
        sar_metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> CrossModalValidationResult:
        """
        Executes end-to-end validation of an Optical-SAR pair.
        Enforces:
        - optical_image is OPTICAL or MULTISPECTRAL
        - sar_image is SAR
        - spatial overlap compatibility
        - raster technical validity
        """
        warnings: List[str] = []

        # 1. Modality detection
        opt_mod = cls.detect_modality(optical_image, optical_metadata)
        sar_mod = cls.detect_modality(sar_image, sar_metadata)
        sar_pol = cls.detect_sar_polarization(sar_image, sar_metadata)

        # Check if user swapped order (first is SAR, second is Optical)
        if opt_mod == MODALITY_SAR and sar_mod in SUPPORTED_OPTICAL_MODALITIES:
            return CrossModalValidationResult(
                valid=False,
                optical_valid=False,
                sar_valid=False,
                spatially_compatible=False,
                overlap_ratio=0.0,
                status_code="MODALITY_ORDER_SWAPPED",
                message="Image 1 was detected as SAR and Image 2 was detected as Optical. Please assign them to their respective optical and SAR slots.",
                optical_modality=opt_mod,
                sar_modality=sar_mod,
                sar_polarization=sar_pol,
                warnings=["Optical and SAR images appear inverted in input parameters."]
            )

        # Reject Optical + Optical
        if opt_mod in SUPPORTED_OPTICAL_MODALITIES and sar_mod in SUPPORTED_OPTICAL_MODALITIES:
            return CrossModalValidationResult(
                valid=False,
                optical_valid=True,
                sar_valid=False,
                spatially_compatible=False,
                overlap_ratio=0.0,
                status_code="INVALID_SAR_MODALITY",
                message="Both images were identified as Optical/Multispectral. Cross-modal analysis requires one Optical image and one SAR image. Use Temporal Analysis for bi-temporal optical pairs.",
                optical_modality=opt_mod,
                sar_modality=sar_mod,
                sar_polarization=None,
                warnings=["Rejected duplicate optical modality pair in cross-modal endpoint."]
            )

        # Reject SAR + SAR
        if opt_mod == MODALITY_SAR and sar_mod == MODALITY_SAR:
            return CrossModalValidationResult(
                valid=False,
                optical_valid=False,
                sar_valid=True,
                spatially_compatible=False,
                overlap_ratio=0.0,
                status_code="INVALID_OPTICAL_MODALITY",
                message="Both images were identified as SAR. Cross-modal analysis requires one Optical image and one SAR image.",
                optical_modality=opt_mod,
                sar_modality=sar_mod,
                sar_polarization=sar_pol,
                warnings=["Rejected duplicate SAR modality pair in cross-modal endpoint."]
            )

        # Check unknown modalities
        if opt_mod == MODALITY_UNKNOWN:
            return CrossModalValidationResult(
                valid=False,
                optical_valid=False,
                sar_valid=(sar_mod == MODALITY_SAR),
                spatially_compatible=False,
                overlap_ratio=0.0,
                status_code="UNKNOWN_OPTICAL_MODALITY",
                message=f"Could not determine modality for optical candidate image '{optical_image.original_filename}'.",
                optical_modality=opt_mod,
                sar_modality=sar_mod,
                sar_polarization=sar_pol,
                warnings=["Optical candidate modality is UNKNOWN."]
            )

        if sar_mod == MODALITY_UNKNOWN:
            return CrossModalValidationResult(
                valid=False,
                optical_valid=(opt_mod in SUPPORTED_OPTICAL_MODALITIES),
                sar_valid=False,
                spatially_compatible=False,
                overlap_ratio=0.0,
                status_code="UNKNOWN_SAR_MODALITY",
                message=f"Could not determine modality for SAR candidate image '{sar_image.original_filename}'.",
                optical_modality=opt_mod,
                sar_modality=sar_mod,
                sar_polarization=sar_pol,
                warnings=["SAR candidate modality is UNKNOWN."]
            )

        # 2. Independent technical validation
        opt_valid, opt_issues = cls.validate_optical(optical_image)
        sar_valid, sar_issues = cls.validate_sar(sar_image)

        if not opt_valid:
            warnings.extend(opt_issues)
        if not sar_valid:
            warnings.extend(sar_issues)

        # 3. Spatial overlap & compatibility evaluation
        spatial_result = CrossModalSpatialCompatibility.evaluate(
            optical_image=optical_image,
            sar_image=sar_image
        )

        spatially_compatible = spatial_result["is_compatible"]
        overlap_ratio = spatial_result["overlap_ratio"]

        if not spatially_compatible:
            warnings.append(spatial_result["message"])
        elif spatial_result["compatibility"] == "PARTIALLY_COMPATIBLE":
            warnings.append(f"Partial overlap ({round(overlap_ratio * 100, 1)}%): analysis will be restricted to intersecting footprint.")

        overall_valid = opt_valid and sar_valid and spatially_compatible

        status_code = "VALID" if overall_valid else ("SPATIAL_MISMATCH" if not spatially_compatible else "INVALID_IMAGE_DATA")
        msg = "Optical-SAR pair validated successfully." if overall_valid else (
            spatial_result["message"] if not spatially_compatible else "Image technical validation failed."
        )

        return CrossModalValidationResult(
            valid=overall_valid,
            optical_valid=opt_valid,
            sar_valid=sar_valid,
            spatially_compatible=spatially_compatible,
            overlap_ratio=overlap_ratio,
            status_code=status_code,
            message=msg,
            optical_modality=opt_mod,
            sar_modality=sar_mod,
            sar_polarization=sar_pol,
            warnings=warnings
        )
