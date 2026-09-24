import pytest
from pathlib import Path
from app.geospatial.validator import GeospatialValidator
from app.core.security import validate_file_extension, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("../../../malicious_file.tif") == "malicious_file.tif"
    assert sanitize_filename("safe_image.png") == "safe_image.png"
    assert sanitize_filename("invalid\x00name.jpg") == "invalidname.jpg"


def test_validate_file_extension():
    assert validate_file_extension("test.tif")[0] is True
    assert validate_file_extension("test.TIFF")[0] is True
    assert validate_file_extension("test.png")[0] is True
    assert validate_file_extension("test.jpg")[0] is True
    assert validate_file_extension("test.jpeg")[0] is True
    assert validate_file_extension("test.exe")[0] is False
    assert validate_file_extension("test.sh")[0] is False
    assert validate_file_extension("test.pdf")[0] is False


def test_corrupted_file_validation(fixtures_dir: Path):
    corrupt_file = fixtures_dir / "corrupted.tif"
    if corrupt_file.exists():
        data = corrupt_file.read_bytes()
        res = GeospatialValidator.validate_file_content(data, "corrupted.tif")
        assert res.valid is False
        assert len(res.errors) > 0


def test_unsupported_file_content(fixtures_dir: Path):
    txt_file = fixtures_dir / "invalid.txt"
    if txt_file.exists():
        data = txt_file.read_bytes()
        res = GeospatialValidator.validate_file_content(data, "invalid.txt")
        assert res.valid is False
        assert len(res.errors) > 0


def test_png_validation(fixtures_dir: Path):
    png_file = fixtures_dir / "sample.png"
    if png_file.exists():
        data = png_file.read_bytes()
        res = GeospatialValidator.validate_file_content(data, "sample.png")
        assert res.valid is True
        assert res.format_name == "PNG"
        assert res.is_geospatial is False


def test_jpeg_validation(fixtures_dir: Path):
    jpg_file = fixtures_dir / "sample.jpg"
    if jpg_file.exists():
        data = jpg_file.read_bytes()
        res = GeospatialValidator.validate_file_content(data, "sample.jpg")
        assert res.valid is True
        assert res.format_name == "JPEG"
        assert res.is_geospatial is False
