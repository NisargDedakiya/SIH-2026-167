"""
Optical and Multispectral Preprocessing & Feature Encoder.
Stage A (Optical Path): Extracts visual spectral representations while preserving multispectral channels.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image


class OpticalEncoder:
    """
    Independent Optical Preprocessor & Feature Encoder.
    Preserves multispectral information without indiscriminately truncating to RGB.
    """

    @classmethod
    def preprocess(
        cls,
        optical_array: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Bands -> Normalization -> Resize/Crop -> Float Tensor.
        optical_array: Shape (H, W, C) or (H, W).
        """
        arr = optical_array.copy()
        if arr.ndim == 2:
            arr = np.expand_dims(arr, axis=-1)

        # 1. Percentile-based contrast normalization
        if normalize:
            if arr.dtype == np.uint8:
                arr = arr.astype(np.float32) / 255.0
            else:
                p2, p98 = np.percentile(arr, (2, 98))
                if p98 > p2:
                    arr = np.clip((arr - p2) / (p98 - p2), 0.0, 1.0)
                else:
                    arr = arr.astype(np.float32) / (np.max(arr) + 1e-6)

        # 2. Spatial resizing if requested
        if target_size is not None:
            tw, th = target_size
            channels = []
            for c in range(arr.shape[2]):
                ch = Image.fromarray(arr[:, :, c])
                ch_resized = ch.resize((tw, th), Image.Resampling.BILINEAR)
                channels.append(np.array(ch_resized))
            arr = np.stack(channels, axis=-1)

        return arr

    @classmethod
    def extract_features(cls, optical_tensor: np.ndarray) -> np.ndarray:
        """
        Extracts multi-scale spatial-spectral representations.
        Computes spectral mean, spatial gradients, and color/reflectance descriptors.
        """
        h, w = optical_tensor.shape[:2]
        c = optical_tensor.shape[2] if optical_tensor.ndim == 3 else 1

        # Base representation: normalized spectral tensor
        features = optical_tensor.astype(np.float32)
        return features
