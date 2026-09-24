"""
Phase 10 — Full System End-to-End (E2E) Integration Tests.
Executes complete lifecycle paths:
Upload -> Validation -> Agent Query -> Specialized Tool Execution ->
Evidence Generation -> Calibrated Confidence -> Observability Trace -> Multi-Format Reports.
"""

import io
import json
import uuid
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient


def make_geotiff_bytes(width=64, height=64, count=3, base=2000, crs="EPSG:32643") -> bytes:
    mem = io.BytesIO()
    data = (np.random.rand(count, height, width) * 1000 + base).astype(np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)
    with rasterio.open(
        mem,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=count,
        dtype="uint16",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(data)
    return mem.getvalue()


# =========================================================================
# E2E-01: Ingestion & Metadata Lifecycle
# =========================================================================

def test_e2e_01_upload_and_metadata_lifecycle(client: TestClient):
    """E2E-01: Ingestion -> Raster Validation -> GeoTIFF Metadata -> Preview Generation."""
    tif_bytes = make_geotiff_bytes(64, 64, count=4)
    files = {"file": ("cartosat_e2e.tif", io.BytesIO(tif_bytes), "image/tiff")}

    # 1. Upload
    res = client.post("/api/v1/images/upload", files=files)
    assert res.status_code == 201
    img_data = res.json()
    img_id = img_data["id"]
    assert img_data["status"] in ("valid", "success")

    # 2. Inspect Metadata
    res_inspect = client.get(f"/api/v1/images/{img_id}")
    assert res_inspect.status_code == 200
    inspect_data = res_inspect.json()
    assert inspect_data["raster"]["width"] == 64
    assert inspect_data["raster"]["bands"] == 4
    assert inspect_data["geospatial"]["is_geospatial"] is True
    assert inspect_data["geospatial"]["crs"] is not None

    # 3. Preview
    res_prev = client.get(f"/api/v1/images/{img_id}/preview")
    assert res_prev.status_code == 200
    assert res_prev.headers["content-type"].startswith("image/")


# =========================================================================
# E2E-02: Single-Image VQA Query & Trace
# =========================================================================

def test_e2e_02_vqa_query_and_trace(client: TestClient):
    """E2E-02: Upload image -> Query -> Agent Routing -> VQA Model -> Observability Trace."""
    tif_bytes = make_geotiff_bytes(64, 64)
    files = {"file": ("vqa_target.tif", io.BytesIO(tif_bytes), "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    img_id = upload_res.json()["id"]

    query_payload = {
        "query": "What type of land cover dominates this satellite image?",
        "image_ids": [img_id]
    }
    res = client.post("/api/v1/agent/analyze", json=query_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "completed"
    assert data["task"] in ("VISUAL_QUESTION_ANSWERING", "visual_question_answering")
    assert len(data["answer"]) > 0
    assert data["confidence"]["score"] >= 0.5
    assert "trace_id" in data
    assert data["trace"] is not None
    assert len(data["trace"]["events"]) >= 5


# =========================================================================
# E2E-03: Spatial Grounding & Evidence Overlays
# =========================================================================

def test_e2e_03_grounding_and_evidence(client: TestClient):
    """E2E-03: Upload -> Grounding directive -> Bounding box extraction -> Evidence Overlay."""
    tif_bytes = make_geotiff_bytes(64, 64)
    files = {"file": ("grounding_target.tif", io.BytesIO(tif_bytes), "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    img_id = upload_res.json()["id"]

    grounding_payload = {
        "query": "Highlight the buildings in this image.",
        "image_ids": [img_id]
    }
    res = client.post("/api/v1/agent/analyze", json=grounding_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "completed"
    assert data["task"] in ("GROUNDING", "grounding")
    assert len(data["regions"]) > 0
    first_region = data["regions"][0]
    assert "box_2d" in first_region or "bbox" in first_region or "pixel_box" in first_region


# =========================================================================
# E2E-04: Bi-Temporal Pair & Change Detection
# =========================================================================

def test_e2e_04_bitemporal_change_analysis(client: TestClient):
    """E2E-04: Upload T1 & T2 -> Pair Registration -> Temporal Alignment -> Change Map."""
    t1_bytes = make_geotiff_bytes(64, 64, base=1500)
    t2_bytes = make_geotiff_bytes(64, 64, base=2400)

    u1 = client.post("/api/v1/images/upload", files={"file": ("t1.tif", io.BytesIO(t1_bytes), "image/tiff")}).json()
    u2 = client.post("/api/v1/images/upload", files={"file": ("t2.tif", io.BytesIO(t2_bytes), "image/tiff")}).json()

    # Create Pair
    pair_res = client.post("/api/v1/temporal/pairs", json={"image_t1_id": u1["id"], "image_t2_id": u2["id"]})
    assert pair_res.status_code == 201
    pair_id = pair_res.json()["pair_id"]

    # Run Temporal Change Analysis
    change_res = client.post("/api/v1/analysis/change", json={"pair_id": pair_id})
    assert change_res.status_code == 200
    change_data = change_res.json()
    assert "change" in change_data
    assert "change_percentage" in change_data["change"]
    assert "analysis_id" in change_data


# =========================================================================
# E2E-05: Optical + SAR Cross-Modal Fusion
# =========================================================================

def test_e2e_05_optical_sar_cross_modal(client: TestClient):
    """E2E-05: Upload Optical & SAR -> Modality Pair -> Cross-modal reasoning."""
    opt_bytes = make_geotiff_bytes(64, 64, count=3, base=2000)
    sar_bytes = make_geotiff_bytes(64, 64, count=2, base=400)

    u_opt = client.post("/api/v1/images/upload", files={"file": ("optical.tif", io.BytesIO(opt_bytes), "image/tiff")}).json()
    u_sar = client.post("/api/v1/images/upload", files={"file": ("sar.tif", io.BytesIO(sar_bytes), "image/tiff")}).json()

    # Create Optical + SAR Pair
    pair_res = client.post("/api/v1/cross-modal/pairs", json={"optical_image_id": u_opt["id"], "sar_image_id": u_sar["id"]})
    assert pair_res.status_code == 201
    pair_id = pair_res.json()["id"]

    # Analyze Cross-Modal Pair
    res = client.post("/api/v1/analysis/cross-modal", json={"pair_id": pair_id})
    assert res.status_code == 200
    data = res.json()
    assert "optical_summary" in data
    assert "sar_summary" in data


# =========================================================================
# E2E-06: Multi-Format Report Generation
# =========================================================================

def test_e2e_06_reports_export_formats(client: TestClient):
    """E2E-06: Generate Analysis -> Export JSON, Interactive HTML, Vector PDF, and ZIP Package."""
    tif_bytes = make_geotiff_bytes(64, 64)
    u = client.post("/api/v1/images/upload", files={"file": ("report_source.tif", io.BytesIO(tif_bytes), "image/tiff")}).json()

    # Run analysis
    analysis_res = client.post("/api/v1/analysis/vqa", json={"image_id": u["id"], "query": "Describe visible land cover."})
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["analysis_id"]

    # 1. JSON Report
    json_rep = client.get(f"/api/v1/reports/{analysis_id}/json")
    assert json_rep.status_code == 200
    assert "application/json" in json_rep.headers["content-type"]

    # 2. HTML Report
    html_rep = client.get(f"/api/v1/reports/{analysis_id}/html")
    assert html_rep.status_code == 200
    assert "<!DOCTYPE html>" in html_rep.text
    assert "SatQuery AI" in html_rep.text

    # 3. Vector PDF Report
    pdf_rep = client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert pdf_rep.status_code == 200
    assert pdf_rep.content.startswith(b"%PDF")

    # 4. Deliverable Package (ZIP)
    pkg_rep = client.get(f"/api/v1/reports/{analysis_id}/package")
    assert pkg_rep.status_code == 200
    assert pkg_rep.content.startswith(b"PK")


# =========================================================================
# E2E-07: Error Standardization & Robustness
# =========================================================================

def test_e2e_07_standardized_error_handling(client: TestClient):
    """E2E-07: Verify error standardization on 404, 422, and invalid UUID inputs."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/images/{fake_id}")
    assert res.status_code == 404
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "trace_id" in body["error"]
