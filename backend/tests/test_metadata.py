import pytest
from pathlib import Path
import numpy as np

from app.geospatial.metadata import MetadataExtractor
from app.geospatial.normalization import normalize_raster_band
from app.geospatial.preview import PreviewGenerator


def test_normalization_bounds():
    # 16-bit simulated satellite band [1000 to 10000]
    data = np.linspace(1000, 10000, 10000, dtype=np.uint16).reshape(100, 100)
    norm = normalize_raster_band(data)

    assert norm.shape == (100, 100)
    assert norm.dtype == np.uint8
    assert norm.min() == 0
    assert norm.max() == 255


def test_normalization_with_nodata():
    data = np.array([[0, 2000], [4000, 8000]], dtype=np.uint16)
    norm = normalize_raster_band(data, nodata=0)
    assert norm[0, 0] == 0  # Nodata remains zeroed


def test_png_metadata_extraction(fixtures_dir: Path):
    png_path = fixtures_dir / "sample.png"
    if png_path.exists():
        data = png_path.read_bytes()
        meta = MetadataExtractor.extract(data, "sample.png")

        assert meta.format_name == "PNG"
        assert meta.is_geospatial is False
        assert meta.crs_str is None
        assert meta.width > 0
        assert meta.height > 0
        assert meta.bands in (3, 4)


def test_preview_generation(fixtures_dir: Path):
    png_path = fixtures_dir / "sample.png"
    if png_path.exists():
        data = png_path.read_bytes()
        preview = PreviewGenerator.generate(data, max_dim=64)

        assert preview.mime_type == "image/png"
        assert preview.width <= 64
        assert preview.height <= 64
        assert len(preview.image_bytes) > 0
