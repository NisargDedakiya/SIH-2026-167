"""
Optical and Multispectral Preprocessing Pipeline for Domain Adaptation.
Handles band projections (RGB, Color-Infrared, SWIR) and percentile contrast normalization.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image

try:
    from training.datasets.bigearthnet.metadata import BAND_PROJECTIONS
except ImportError:
    from app.training.datasets.bigearthnet.metadata import BAND_PROJECTIONS


class OpticalPreprocessor:
    """
    Normalizes and projects raw optical and multispectral remote-sensing bands
    into standardized format for Vision-Language Models.
    """

    @staticmethod
    def percentile_stretch(
        band: np.ndarray,
        lower_percentile: float = 2.0,
        upper_percentile: float = 98.0,
        nodata: Optional[float] = None
    ) -> np.ndarray:
        """
        Applies robust percentile contrast stretching (0 to 255 uint8).
        """
        if nodata is not None:
            valid_mask = band != nodata
            if not np.any(valid_mask):
                return np.zeros_like(band, dtype=np.uint8)
            valid_vals = band[valid_mask]
        else:
            valid_vals = band

        p_low = np.percentile(valid_vals, lower_percentile)
        p_high = np.percentile(valid_vals, upper_percentile)

        if p_high <= p_low:
            p_high = p_low + 1.0

        stretched = (band - p_low) / (p_high - p_low)
        stretched = np.clip(stretched, 0.0, 1.0) * 255.0
        return stretched.astype(np.uint8)

    @classmethod
    def project_bands(
        cls,
        band_dict: Dict[str, np.ndarray],
        projection_type: str = "RGB",
        target_size: Optional[Tuple[int, int]] = None
    ) -> Image.Image:
        """
        Composes 3 specified bands into an RGB image.
        Default projections:
        - 'RGB': B04 (Red), B03 (Green), B02 (Blue)
        - 'COLOR_INFRARED': B08 (NIR), B04 (Red), B03 (Green)
        """
        band_names = BAND_PROJECTIONS.get(projection_type, BAND_PROJECTIONS["RGB"])
        channels = []

        for name in band_names:
            if name in band_dict:
                arr = band_dict[name]
                stretched = cls.percentile_stretch(arr)
            else:
                # If specific band not available, use zero fallback
                shape = next(iter(band_dict.values())).shape if band_dict else (120, 120)
                stretched = np.zeros(shape, dtype=np.uint8)
            channels.append(stretched)

        composite = np.stack(channels, axis=-1)
        img = Image.fromarray(composite, mode="RGB")
        if target_size and img.size != target_size:
            img = img.resize(target_size, Image.Resampling.BILINEAR)
        return img
