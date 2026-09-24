from pathlib import Path
import pytest


def test_upload_invalid_extension(client):
    files = {"file": ("malicious.exe", b"MZ\x90\x00executabledata", "application/x-msdownload")}
    response = client.post("/api/v1/images/upload", files=files)
    assert response.status_code == 400
    assert "Validation failed" in response.json()["detail"]


def test_upload_corrupted_file(client, fixtures_dir: Path):
    corrupt_file = fixtures_dir / "corrupted.tif"
    if corrupt_file.exists():
        files = {"file": ("corrupted.tif", corrupt_file.read_bytes(), "image/tiff")}
        response = client.post("/api/v1/images/upload", files=files)
        assert response.status_code == 400


def test_upload_and_inspect_lifecycle(client, fixtures_dir: Path):
    sample_png = fixtures_dir / "sample.png"
    if not sample_png.exists():
        pytest.skip("sample.png fixture not yet generated")

    # 1. Upload
    files = {"file": ("test_sample.png", sample_png.read_bytes(), "image/png")}
    res_upload = client.post("/api/v1/images/upload", files=files)
    assert res_upload.status_code == 201
    upload_data = res_upload.json()
    image_id = upload_data["id"]
    assert upload_data["filename"] == "test_sample.png"
    assert upload_data["status"] == "valid"

    # 2. Inspect
    res_inspect = client.get(f"/api/v1/images/{image_id}")
    assert res_inspect.status_code == 200
    inspect_data = res_inspect.json()
    assert inspect_data["id"] == image_id
    assert inspect_data["format"] == "PNG"
    assert inspect_data["raster"]["width"] > 0
    assert inspect_data["geospatial"]["is_geospatial"] is False
    assert inspect_data["validation"]["valid"] is True

    # 3. Preview
    res_preview = client.get(f"/api/v1/images/{image_id}/preview")
    assert res_preview.status_code == 200
    assert res_preview.headers["content-type"] == "image/png"
    assert len(res_preview.content) > 0

    # 4. Revalidate
    res_val = client.post(f"/api/v1/images/{image_id}/validate")
    assert res_val.status_code == 200
    assert res_val.json()["valid"] is True

    # 5. Delete
    res_del = client.delete(f"/api/v1/images/{image_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True

    # 6. Verify deleted
    res_notfound = client.get(f"/api/v1/images/{image_id}")
    assert res_notfound.status_code == 404


def test_upload_geotiff_with_crs(client, fixtures_dir: Path):
    geotiff = fixtures_dir / "geotiff_valid.tif"
    if not geotiff.exists():
        pytest.skip("geotiff_valid.tif not present")

    files = {"file": ("geotiff_valid.tif", geotiff.read_bytes(), "image/tiff")}
    res_upload = client.post("/api/v1/images/upload", files=files)
    assert res_upload.status_code == 201
    data = res_upload.json()
    image_id = data["id"]

    res_inspect = client.get(f"/api/v1/images/{image_id}")
    assert res_inspect.status_code == 200
    inspect = res_inspect.json()
    assert inspect["format"] == "GeoTIFF"
    assert inspect["geospatial"]["is_geospatial"] is True
    assert inspect["geospatial"]["epsg"] == 4326
    assert inspect["raster"]["bands"] == 4
    assert inspect["raster"]["dtype"] == "uint16"


def test_upload_tiff_without_crs(client, fixtures_dir: Path):
    tiff = fixtures_dir / "tiff_no_crs.tif"
    if not tiff.exists():
        pytest.skip("tiff_no_crs.tif not present")

    files = {"file": ("tiff_no_crs.tif", tiff.read_bytes(), "image/tiff")}
    res_upload = client.post("/api/v1/images/upload", files=files)
    assert res_upload.status_code == 201
    data = res_upload.json()
    assert data["status"] == "warning"

    res_inspect = client.get(f"/api/v1/images/{data['id']}")
    assert res_inspect.status_code == 200
    inspect = res_inspect.json()
    assert inspect["format"] == "TIFF"
    assert inspect["geospatial"]["is_geospatial"] is False
    assert any("does not contain geospatial referencing" in w for w in inspect["validation"]["warnings"])
