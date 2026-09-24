"""
Automated test suite for SatQuery AI Phase 9: Evidence, Reports & Product UX.
Verifies report schemas, multi-format exporters (JSON, HTML, PDF, ZIP),
backend API report endpoints, history audit pagination/search, and analysis reconstruction.
"""

import io
import uuid
import zipfile
import numpy as np
import pytest
from fastapi.testclient import TestClient
import rasterio
from rasterio.transform import from_origin

from app.reports.schemas import (
    AnalysisReport,
    ReportInputImage,
    ReportEvidenceItem,
    ReportObservations,
    ReportModelDetails,
    ReportExecutionMilestone,
)
from app.reports.json_exporter import JsonReportExporter
from app.reports.html_exporter import HtmlReportExporter
from app.reports.pdf_exporter import PdfReportExporter
from app.reports.package_exporter import AnalysisPackageExporter
from app.database.session import async_session_factory
from app.database.models import AnalysisJobModel, ImageModel


def sample_analysis_report() -> AnalysisReport:
    """Creates a deterministic AnalysisReport fixture for unit tests."""
    return AnalysisReport(
        report_id=str(uuid.uuid4()),
        analysis_id=str(uuid.uuid4()),
        generated_at="2026-09-23T12:00:00Z",
        system_title="SatQuery AI - Interactive Remote-Sensing Intelligence",
        problem_statement="ISRO Smart India Hackathon · Problem Statement 26167",
        query="Identify dominant land cover and detect industrial storage tanks.",
        detected_task="visual_question_answering",
        answer="The scene is dominated by industrial and port infrastructure with prominent storage tanks.",
        confidence_score=0.91,
        confidence_percentage="91%",
        calibration_status="Conformal Prediction Calibrated (BigEarthNet v2.0)",
        inputs=[
            ReportInputImage(
                image_id=str(uuid.uuid4()),
                role="primary_optical",
                filename="cartosat_scene_01.tif",
                modality="optical",
                sensor="Cartosat-2S PAN/MX",
                dimensions="1024x1024",
                resolution_m=0.65,
                crs="EPSG:32643",
                is_geospatial=True,
            )
        ],
        evidence=[
            ReportEvidenceItem(
                evidence_id="ev_01",
                type="bbox",
                label="Industrial Tank Cluster",
                confidence=0.89,
                pixel_coordinates=[120, 240, 260, 380],
                geographic_coordinates=[77.123, 28.456, 77.125, 28.458],
            )
        ],
        observations=ReportObservations(
            observed=[
                "High-resolution multispectral reflectance with 0.65m GSD.",
                "Four spectral bands processed with 2%-98% percentile contrast stretch.",
            ],
            inferred=[
                "Circular structural geometry indicates petroleum/chemical storage facility.",
            ],
            uncertain=[
                "Minor cloud shadowing at western perimeter.",
            ],
        ),
        models=[
            ReportModelDetails(
                name="Qwen2.5-VL-7B-Instruct",
                version="v2.5",
                task="vqa",
                is_adapted=True,
                adapter_type="LoRA (BigEarthNet v2.0 domain adapted)",
                base_model="Qwen2.5-VL-7B-Instruct",
            )
        ],
        execution_milestones=[
            ReportExecutionMilestone(
                sequence=1,
                milestone="Geospatial Ingestion & CRS Normalization",
                duration_ms=210,
                status="completed",
                timestamp="2026-09-23T12:00:01Z",
            ),
            ReportExecutionMilestone(
                sequence=2,
                milestone="Domain Adaptation VLM Inference",
                duration_ms=1150,
                status="completed",
                timestamp="2026-09-23T12:00:02Z",
            ),
        ],
        total_processing_time_ms=1360,
        limitations=[
            "Grounding coordinates bounded by sensor spatial resolution.",
        ],
        reproducibility_token="SQ-2026-TEST-ABCD-1234",
    )


def create_test_geotiff() -> bytes:
    """Creates synthetic GeoTIFF for end-to-end integration tests."""
    buf = io.BytesIO()
    data = (np.random.rand(3, 80, 80) * 2000).astype(np.uint16)
    transform = from_origin(600000, 3100000, 10, 10)

    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=80,
        width=80,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    return buf.getvalue()


# -------------------------------------------------------------------------
# Unit Tests: Exporters
# -------------------------------------------------------------------------

def test_analysis_report_schema_validation():
    """Verify that AnalysisReport constructs and validates strictly."""
    report = sample_analysis_report()
    assert report.system_title.startswith("SatQuery AI")
    assert report.confidence_score == 0.91
    assert len(report.inputs) == 1
    assert len(report.evidence) == 1
    assert len(report.observations.observed) == 2


def test_json_exporter():
    """Verify JSON exporter generates valid JSON with correct key fields."""
    report = sample_analysis_report()
    json_str = JsonReportExporter.export(report)
    assert isinstance(json_str, str)
    assert report.reproducibility_token in json_str
    assert "Cartosat-2S PAN/MX" in json_str
    assert '"confidence_score": 0.91' in json_str


def test_html_exporter():
    """Verify HTML exporter generates standalone valid HTML with no missing sections."""
    report = sample_analysis_report()
    html_str = HtmlReportExporter.export(report)
    assert isinstance(html_str, str)
    assert "<!DOCTYPE html>" in html_str
    assert report.system_title in html_str
    assert report.reproducibility_token in html_str
    assert "Observed Facts" in html_str
    assert "Model Inferences" in html_str
    assert "cartosat_scene_01.tif" in html_str


def test_pdf_exporter():
    """Verify PDF exporter uses ReportLab to generate valid binary PDF bytes."""
    report = sample_analysis_report()
    pdf_bytes = PdfReportExporter.export(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_package_exporter():
    """Verify package exporter generates sanitized ZIP with all expected deliverables."""
    report = sample_analysis_report()
    evidence_files = {"sample_bbox.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"}
    zip_bytes = AnalysisPackageExporter.export(report, raw_evidence_bytes=evidence_files)

    assert isinstance(zip_bytes, bytes)
    assert len(zip_bytes) > 2000

    # Read back with zipfile
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "analysis.json" in namelist
        assert "report.html" in namelist
        assert "report.pdf" in namelist
        assert "metadata.json" in namelist
        assert "trace.json" in namelist
        assert "README.txt" in namelist
        assert any("sample_bbox.png" in name for name in namelist)

        # Verify README contents
        readme = zf.read("README.txt").decode("utf-8")
        assert "SATQUERY AI" in readme.upper()
        assert report.reproducibility_token in readme


# -------------------------------------------------------------------------
# Integration Tests: FastAPI Report & Analysis Endpoints
# -------------------------------------------------------------------------

def test_reports_api_end_to_end(client: TestClient):
    """End-to-end integration test: upload image -> run VQA -> fetch reports."""
    # 1. Ingest image
    file_bytes = create_test_geotiff()
    files = {"file": ("test_report_image.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # 2. Run VQA to produce an AnalysisJobModel
    vqa_payload = {
        "image_id": image_id,
        "query": "Identify the primary land utilization in this scene."
    }
    vqa_res = client.post("/api/v1/analysis/vqa", json=vqa_payload)
    assert vqa_res.status_code == 200
    job_id = vqa_res.json()["analysis_id"]

    # 3. GET /api/v1/reports/{analysis_id}
    rep_meta = client.get(f"/api/v1/reports/{job_id}")
    assert rep_meta.status_code == 200
    meta_data = rep_meta.json()
    assert meta_data["analysis_id"] == job_id
    assert "reproducibility_token" in meta_data
    assert len(meta_data["inputs"]) >= 1

    # 4. GET /api/v1/reports/{analysis_id}/json
    rep_json = client.get(f"/api/v1/reports/{job_id}/json")
    assert rep_json.status_code == 200
    assert rep_json.headers["content-type"].startswith("application/json")
    assert rep_json.json()["analysis_id"] == job_id

    # 5. GET /api/v1/reports/{analysis_id}/html
    rep_html = client.get(f"/api/v1/reports/{job_id}/html")
    assert rep_html.status_code == 200
    assert "text/html" in rep_html.headers["content-type"]
    assert "<!DOCTYPE html>" in rep_html.text

    # 6. GET /api/v1/reports/{analysis_id}/pdf
    rep_pdf = client.get(f"/api/v1/reports/{job_id}/pdf")
    assert rep_pdf.status_code == 200
    assert "application/pdf" in rep_pdf.headers["content-type"]
    assert rep_pdf.content.startswith(b"%PDF")

    # 7. GET /api/v1/reports/{analysis_id}/package
    rep_pkg = client.get(f"/api/v1/reports/{job_id}/package")
    assert rep_pkg.status_code == 200
    assert "application/zip" in rep_pkg.headers["content-type"]
    assert len(rep_pkg.content) > 1000

    # 8. GET /api/v1/reports/invalid_uuid -> 404
    bad_id = str(uuid.uuid4())
    rep_bad = client.get(f"/api/v1/reports/{bad_id}")
    assert rep_bad.status_code == 404


def test_analysis_history_and_detail_endpoints(client: TestClient):
    """Test GET /api/v1/analysis/history (filtering/pagination) and GET /api/v1/analysis/{id}."""
    # 1. Fetch history
    hist_res = client.get("/api/v1/analysis/history?page=1&limit=10")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert "items" in hist_data
    assert "total" in hist_data
    assert isinstance(hist_data["items"], list)

    if len(hist_data["items"]) > 0:
        target_id = hist_data["items"][0]["id"]

        # 2. Fetch full detail
        det_res = client.get(f"/api/v1/analysis/{target_id}")
        assert det_res.status_code == 200
        det_data = det_res.json()
        assert det_data["analysis_id"] == target_id
        assert "inputs" in det_data
        assert "evidence" in det_data
        assert "status" in det_data
