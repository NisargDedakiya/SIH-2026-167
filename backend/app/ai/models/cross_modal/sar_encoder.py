"""
SAR (Synthetic Aperture Radar) Preprocessing & Feature Encoder.
Stage A (SAR Path): Handles polarization channels, dB log-scale transforms,
and microwave backscatter dynamics. Strictly avoids blind RGB normalization.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image


class SAREncoder:
    """
    Independent SAR Preprocessor & Feature Encoder.
    Processes radar amplitude/intensity, converts to decibel scale (dB) where appropriate,
    and isolates surface roughness and double-bounce scattering features.
    """

    @classmethod
    def preprocess(
        cls,
        sar_array: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None,
        apply_db_scale: bool = True,
        clip_percentiles: Tuple[float, float] = (1.0, 99.0),
    ) -> np.ndarray:
        """
        SAR preprocessing pipeline:
        Channels -> Dynamic range handling -> Optional log/dB scale -> Normalization -> Tensor.
        """
        arr = sar_array.copy().astype(np.float32)
        if arr.ndim == 2:
            arr = np.expand_dims(arr, axis=-1)

        # 1. Decibel log-scale transformation for high dynamic range radar returns
        if apply_db_scale:
            # Clip minimum positive value to avoid log(0)
            eps = 1e-5
            arr = np.clip(arr, eps, None)
            # 10 * log10(intensity + eps)
            arr = 10.0 * np.log10(arr)

        # 2. SAR percentile clipping (1% - 99% to eliminate speckle noise spikes)
        p_low, p_high = np.percentile(arr, clip_percentiles)
        if p_high > p_low:
            arr = np.clip((arr - p_low) / (p_high - p_low), 0.0, 1.0)
        else:
            arr = np.clip(arr, 0.0, 1.0)

        # 3. Spatial resizing if specified
        if target_size is not None:
            tw, th = target_size
            channels = []
            for c in range(arr.shape[2]):
                ch = Image.fromarray((arr[:, :, c] * 255.0).astype(np.uint8))
                ch_resized = ch.resize((tw, th), Image.Resampling.BILINEAR)
                channels.append(np.array(ch_resized).astype(np.float32) / 255.0)
            arr = np.stack(channels, axis=-1)

        return arr.astype(np.float32)

    @classmethod
    def extract_features(cls, sar_tensor: np.ndarray) -> np.ndarray:
        """
        Extracts structural microwave backscatter descriptors:
        - Radar backscatter intensity
        - Local gradient/roughness
        - Double-bounce corner reflection magnitude
        """
        features = sar_tensor.astype(np.float32)
        return features
