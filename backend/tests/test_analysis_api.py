"""
Integration tests for SatQuery Remote-Sensing Analysis API (VQA, Captioning, Job Tracking).
"""

import io
import uuid
import numpy as np
import pytest
from fastapi.testclient import TestClient
import rasterio
from rasterio.transform import from_origin

from app.database.models import AnalysisJobModel
from app.database.session import async_session_factory
from sqlalchemy import select


def create_test_geotiff() -> bytes:
    buf = io.BytesIO()
    data = (np.random.rand(3, 100, 100) * 2000).astype(np.uint16)
    transform = from_origin(600000, 3100000, 10, 10)

    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=100,
        width=100,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    return buf.getvalue()


def test_vqa_api_end_to_end(client: TestClient):
    # 1. Upload satellite GeoTIFF image
    file_bytes = create_test_geotiff()
    files = {"file": ("test_satellite.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # 2. Execute VQA request
    vqa_payload = {
        "image_id": image_id,
        "query": "What type of land cover is visible in this image?"
    }
    vqa_res = client.post("/api/v1/analysis/vqa", json=vqa_payload)
    assert vqa_res.status_code == 200
    vqa_data = vqa_res.json()

    assert vqa_data["task"] == "visual_question_answering"
    assert vqa_data["status"] == "completed"
    assert "answer" in vqa_data and len(vqa_data["answer"]) > 0
    assert "confidence" in vqa_data and vqa_data["confidence"] > 0
    assert "confidence_method" in vqa_data
    assert "model" in vqa_data
    assert "processing_time_ms" in vqa_data
    assert isinstance(vqa_data["evidence"], list)

    # 3. Retrieve analysis job directly via API
    job_res = client.get(f"/api/v1/analysis/jobs/{vqa_data['analysis_id']}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "completed"
    assert job_data["image_id"] == image_id
    assert job_data["task"] == "visual_question_answering"


def test_caption_api_end_to_end(client: TestClient):
    # 1. Upload image
    file_bytes = create_test_geotiff()
    files = {"file": ("caption_scene.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    image_id = upload_res.json()["id"]

    # 2. Request scene description
    cap_res = client.post("/api/v1/analysis/caption", json={"image_id": image_id})
    assert cap_res.status_code == 200
    cap_data = cap_res.json()

    assert cap_data["task"] == "image_captioning"
    assert cap_data["status"] == "completed"
    assert "caption" in cap_data and len(cap_data["caption"]) > 0
    assert cap_data["confidence"] > 0
    assert "model" in cap_data
    assert isinstance(cap_data["evidence"], list)

    # 3. Verify job retrieval endpoint
    job_res = client.get(f"/api/v1/analysis/jobs/{cap_data['analysis_id']}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "completed"
    assert job_data["task"] == "image_captioning"


def test_vqa_validation_errors(client: TestClient):
    # Empty query validation
    empty_q_res = client.post("/api/v1/analysis/vqa", json={
        "image_id": str(uuid.uuid4()),
        "query": "   "
    })
    assert empty_q_res.status_code == 400

    # Non-existent image ID
    missing_img_res = client.post("/api/v1/analysis/vqa", json={
        "image_id": str(uuid.uuid4()),
        "query": "What objects are visible?"
    })
    assert missing_img_res.status_code == 404
    assert "not found" in missing_img_res.json()["detail"].lower()


def test_models_registry_endpoint(client: TestClient):
    res = client.get("/api/v1/analysis/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 2
    tasks = [m["task"] for m in models]
    assert "visual_question_answering" in tasks
    assert "image_captioning" in tasks


def test_list_image_jobs_endpoint(client: TestClient):
    # Upload image
    file_bytes = create_test_geotiff()
    files = {"file": ("jobs_scene.tif", file_bytes, "image/tiff")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    image_id = upload_res.json()["id"]

    # Run caption
    client.post("/api/v1/analysis/caption", json={"image_id": image_id})

    # Run VQA
    client.post("/api/v1/analysis/vqa", json={"image_id": image_id, "query": "What is here?"})

    # List image jobs
    jobs_res = client.get(f"/api/v1/analysis/image/{image_id}/jobs")
    assert jobs_res.status_code == 200
    jobs_list = jobs_res.json()
    assert len(jobs_list) == 2
