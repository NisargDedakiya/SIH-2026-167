"""
Domain Models and Constants for Optical-SAR Cross-Modal Subsystem.
"""

from typing import Final, List
from app.database.models import OpticalSARPairModel

# Export domain entity
OpticalSARPair = OpticalSARPairModel

# Modality definitions
MODALITY_OPTICAL: Final[str] = "optical"
MODALITY_MULTISPECTRAL: Final[str] = "multispectral"
MODALITY_SAR: Final[str] = "sar"
MODALITY_UNKNOWN: Final[str] = "unknown"

SUPPORTED_OPTICAL_MODALITIES: Final[List[str]] = [MODALITY_OPTICAL, MODALITY_MULTISPECTRAL]
SUPPORTED_SAR_MODALITIES: Final[List[str]] = [MODALITY_SAR]

# Polarization types
POLARIZATION_VV: Final[str] = "VV"
POLARIZATION_VH: Final[str] = "VH"
POLARIZATION_HH: Final[str] = "HH"
POLARIZATION_HV: Final[str] = "HV"
POLARIZATION_DUAL: Final[str] = "dual-pol"
POLARIZATION_QUAD: Final[str] = "quad-pol"
POLARIZATION_SINGLE: Final[str] = "single-pol"
POLARIZATION_UNKNOWN: Final[str] = "unknown"

# Spatial compatibility states
COMPATIBILITY_COMPATIBLE: Final[str] = "COMPATIBLE"
COMPATIBILITY_PARTIALLY_COMPATIBLE: Final[str] = "PARTIALLY_COMPATIBLE"
COMPATIBILITY_INCOMPATIBLE: Final[str] = "INCOMPATIBLE"
COMPATIBILITY_INSUFFICIENT_METADATA: Final[str] = "INSUFFICIENT_METADATA"

# Disagreement states
DISAGREEMENT_AGREEMENT: Final[str] = "AGREEMENT"
DISAGREEMENT_PARTIAL: Final[str] = "PARTIAL_AGREEMENT"
DISAGREEMENT_DISAGREEMENT: Final[str] = "DISAGREEMENT"
DISAGREEMENT_INSUFFICIENT: Final[str] = "INSUFFICIENT_EVIDENCE"
