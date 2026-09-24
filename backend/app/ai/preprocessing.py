"""
Remote-Sensing Image Preprocessing Pipeline for AI Inference.

Converts multi-band, arbitrary bit-depth (uint8, uint16, float32) satellite rasters
into standardized RGB PIL Images / Tensors expected by vision-language models.
Preserves the original raster without mutation.
"""

import io
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
import rasterio
from rasterio.io import MemoryFile

from app.ai.exceptions import PreprocessingError
from app.core.logging import logger


class RemoteSensingPreprocessor:
    """
    Geospatial-aware image preprocessor for remote sensing AI inference.
    Handles dynamic bit-depth scaling, multispectral band selection,
    percentile clipping, and aspect-preserving resizing.
    """

    @classmethod
    def read_and_normalize_bands(
        cls,
        image_bytes: bytes,
        selected_bands: Optional[List[int]] = None,
        percentiles: Tuple[float, float] = (2.0, 98.0),
        target_size: Optional[Tuple[int, int]] = (384, 384),
        nodata: Optional[float] = None
    ) -> Image.Image:
        """
        Reads satellite raster bytes, extracts 1-3 appropriate bands,
        applies percentile contrast stretching, scales to uint8 [0, 255],
        and returns an RGB PIL Image ready for VLM processors.
        """
        try:
            with MemoryFile(image_bytes) as memfile:
                with memfile.open() as src:
                    band_count = src.count
                    width = src.width
                    height = src.height

                    # Select bands
                    if selected_bands:
                        bands_to_read = [b for b in selected_bands if 1 <= b <= band_count]
                    elif band_count >= 3:
                        bands_to_read = [1, 2, 3]  # Standard RGB or first 3 bands
                    elif band_count == 2:
                        bands_to_read = [1, 2, 1]  # Replicate first band for 3-channel
                    else:
                        bands_to_read = [1, 1, 1]  # Monoband / SAR / grayscale -> 3-channel RGB

                    # Read bands as float32 for high-dynamic-range scaling
                    raw_bands = []
                    for b_idx in bands_to_read:
                        arr = src.read(b_idx).astype(np.float32)

                        # Mask nodata if present
                        nd = nodata if nodata is not None else src.nodata
                        if nd is not None and not np.isnan(nd):
                            valid_mask = (arr != nd) & np.isfinite(arr)
                        else:
                            valid_mask = np.isfinite(arr)

                        if np.any(valid_mask):
                            p_low, p_high = np.percentile(
                                arr[valid_mask], [percentiles[0], percentiles[1]]
                            )
                            if p_high > p_low:
                                clipped = np.clip(arr, p_low, p_high)
                                normalized = ((clipped - p_low) / (p_high - p_low) * 255.0).astype(np.uint8)
                            else:
                                normalized = np.zeros_like(arr, dtype=np.uint8)
                        else:
                            normalized = np.zeros_like(arr, dtype=np.uint8)

                        raw_bands.append(normalized)

                    # Stack channels (Height, Width, Channels)
                    stacked = np.stack(raw_bands, axis=-1)

                    # Convert to PIL Image
                    pil_img = Image.fromarray(stacked, mode="RGB")

                    # Intelligent aspect-preserving resize with padding or center crop
                    if target_size:
                        pil_img = cls.resize_preserve_aspect(pil_img, target_size)

                    return pil_img

        except Exception as e:
            logger.error(f"Remote sensing preprocessing failed: {e}")
            raise PreprocessingError(f"Raster preprocessing error: {str(e)}") from e

    @staticmethod
    def resize_preserve_aspect(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resizes image to target dimensions preserving aspect ratio with bicubic interpolation.
        """
        target_w, target_h = target_size
        img_w, img_h = image.size

        # Fit within bounding box
        ratio = min(target_w / img_w, target_h / img_h)
        new_w = max(1, int(img_w * ratio))
        new_h = max(1, int(img_h * ratio))

        resized = image.resize((new_w, new_h), Image.Resampling.BICUBIC)

        # Pad onto neutral dark canvas to reach exact target square if needed
        final_image = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        final_image.paste(resized, (offset_x, offset_y))

        return final_image
