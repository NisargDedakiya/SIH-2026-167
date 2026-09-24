from typing import Optional
import numpy as np


def normalize_raster_band(
    band_array: np.ndarray,
    nodata: Optional[float] = None,
    p_low: float = 2.0,
    p_high: float = 98.0
) -> np.ndarray:
    """
    Perform 2% - 98% percentile contrast stretching on a single raster band.
    Transforms raw remote-sensing values (e.g., uint16, float32) into 8-bit [0, 255]
    visualization space while filtering out nodata and extreme sensor outliers.
    """
    if band_array.size == 0:
        return np.zeros_like(band_array, dtype=np.uint8)

    # Convert to float for safe processing
    data = band_array.astype(np.float32)

    # Mask nodata and NaNs/Infs
    mask = np.isfinite(data)
    if nodata is not None:
        mask = mask & (data != nodata)

    valid_pixels = data[mask]
    if valid_pixels.size == 0:
        return np.zeros(band_array.shape, dtype=np.uint8)

    # Calculate percentile bounds
    vmin = np.percentile(valid_pixels, p_low)
    vmax = np.percentile(valid_pixels, p_high)

    if vmax <= vmin:
        # Uniform or flat band
        vmin = np.min(valid_pixels)
        vmax = np.max(valid_pixels)

    if vmax > vmin:
        scaled = (data - vmin) / (vmax - vmin)
        scaled = np.clip(scaled * 255.0, 0, 255)
    else:
        scaled = np.zeros_like(data)

    # Zero-out masked nodata regions
    scaled[~mask] = 0

    return scaled.astype(np.uint8)
