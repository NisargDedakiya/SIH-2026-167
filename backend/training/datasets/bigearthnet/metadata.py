"""
BigEarthNet v2.0 Dataset Metadata, Class Nomenclature, and Sensor Band Specifications.
Ref: BigEarthNet v2.0 (Sentinel-1 and Sentinel-2 Paired Benchmark).
"""

from typing import Dict, List

# CORINE Land Cover (CLC) 19-Class Nomenclature for BigEarthNet
BIGEARTHNET_19_CLASSES: List[str] = [
    "Urban fabric",
    "Industrial or commercial units",
    "Arable land",
    "Permanent crops",
    "Pastures",
    "Complex cultivation patterns",
    "Land principally occupied by agriculture, with significant areas of natural vegetation",
    "Agro-forestry areas",
    "Broad-leaved forest",
    "Coniferous forest",
    "Mixed forest",
    "Natural grassland and sparsely vegetated areas",
    "Moors, heathland and sclerophyllous vegetation",
    "Sclerophyllous vegetation",
    "Transitional woodland, shrub",
    "Beaches, dunes, sands",
    "Inland wetlands",
    "Coastal wetlands",
    "Water bodies",
]

# Sentinel-2 Multispectral Band Specifications (12 bands)
SENTINEL2_BANDS: Dict[str, Dict[str, any]] = {
    "B01": {"name": "Coastal aerosol", "central_wavelength_nm": 443, "resolution_m": 60},
    "B02": {"name": "Blue", "central_wavelength_nm": 490, "resolution_m": 10},
    "B03": {"name": "Green", "central_wavelength_nm": 560, "resolution_m": 10},
    "B04": {"name": "Red", "central_wavelength_nm": 665, "resolution_m": 10},
    "B05": {"name": "Vegetation Red Edge 1", "central_wavelength_nm": 705, "resolution_m": 20},
    "B06": {"name": "Vegetation Red Edge 2", "central_wavelength_nm": 740, "resolution_m": 20},
    "B07": {"name": "Vegetation Red Edge 3", "central_wavelength_nm": 783, "resolution_m": 20},
    "B08": {"name": "NIR (Near Infrared)", "central_wavelength_nm": 842, "resolution_m": 10},
    "B8A": {"name": "Narrow NIR", "central_wavelength_nm": 865, "resolution_m": 20},
    "B09": {"name": "Water vapour", "central_wavelength_nm": 945, "resolution_m": 60},
    "B11": {"name": "SWIR 1", "central_wavelength_nm": 1610, "resolution_m": 20},
    "B12": {"name": "SWIR 2", "central_wavelength_nm": 2190, "resolution_m": 20},
}

# Sentinel-1 SAR Channel Specifications
SENTINEL1_CHANNELS: Dict[str, str] = {
    "VV": "Vertical transmit, Vertical receive (co-polarization, surface roughness/soil)",
    "VH": "Vertical transmit, Horizontal receive (cross-polarization, vegetation volume scattering)",
}

# Standard Band Mappings for Vision-Language Models
BAND_PROJECTIONS: Dict[str, List[str]] = {
    "RGB": ["B04", "B03", "B02"],             # True color (Red, Green, Blue)
    "COLOR_INFRARED": ["B08", "B04", "B03"],   # False color CIR (NIR, Red, Green for vegetation)
    "SWIR_URBAN": ["B12", "B11", "B04"],       # SWIR urban & moisture composition
}
