"""
Integration and regression test suite for SatQuery AI runtime fixes:
1. GET /api/v1/images schema compliance, limit handling, and resilience.
2. Model registry population and specialist model registration.
3. Grounding model error preservation (503 MODEL_UNAVAILABLE instead of 500).
4. End-to-end agent grounding execution on satellite raster.
5. Health and readiness endpoints state verification.
"""

from pathlib import Path
import pytest
from fastapi import HTTPException
from app.ai.exceptions import ModelUnavailableError
from app.ai.runtime import get_model_runtime
from app.agent.executor import ToolExecutor
from app.agent.schemas import WorkflowPlanSchema, PlanStepSchema
from app.agent.trace import ExecutionTrace
from app.schemas.image import ImageInspectResponse


def test_list_images_existing_database(client, fixtures_dir: Path):
    """
    Requirement 7: Integration test verifying GET /api/v1/images?limit=100:
    - Ingests a valid satellite raster.
    - Queries /api/v1/images?limit=100.
    - Validates HTTP 200.
    - Validates full ImageInspectResponse contract.
    - Validates raster specs, geospatial specs, and validation status.
    """
    sample_png = fixtures_dir / "sample.png"
    if not sample_png.exists():
        pytest.skip("sample.png fixture not available")

    # Ingest image
    files = {"file": ("test_runtime_sample.png", sample_png.read_bytes(), "image/png")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    uploaded_id = upload_res.json()["id"]

    # List images with limit=100
    res = client.get("/api/v1/images?limit=100")
    assert res.status_code == 200
    images = res.json()
    assert isinstance(images, list)
    assert len(images) > 0

    # Locate uploaded image in response
    target = next((img for img in images if img["id"] == uploaded_id), None)
    assert target is not None

    # Validate response schema contract
    assert "id" in target
    assert "filename" in target
    assert "format" in target
    assert "size_bytes" in target
    assert "modality" in target

    # Validate raster specs
    raster = target["raster"]
    assert "width" in raster and raster["width"] > 0
    assert "height" in raster and raster["height"] > 0
    assert "bands" in raster and raster["bands"] >= 1
    assert "dtype" in raster

    # Validate geospatial specs
    geo = target["geospatial"]
    assert "is_geospatial" in geo
    assert "bounds" in geo
    assert "resolution" in geo
    assert "transform" in geo

    # Validate validation report
    val = target["validation"]
    assert "valid" in val
    assert "warnings" in val
    assert isinstance(val["warnings"], list)
    assert "errors" in val
    assert isinstance(val["errors"], list)


def test_model_registry_non_empty():
    """
    Requirement 23: Verify that get_model_runtime() registers all canonical models:
    - satquery-rs-v1
    - remote-sensing-vqa
    - remote-sensing-caption
    - remote-sensing-grounding
    - remote-sensing-change
    - remote-sensing-cross-modal
    The registry must not be empty.
    """
    runtime = get_model_runtime()
    models = runtime.registry.list_models()
    assert len(models) > 0

    required_models = [
        "satquery-rs-v1",
        "remote-sensing-vqa",
        "remote-sensing-caption",
        "remote-sensing-grounding",
        "remote-sensing-change",
        "remote-sensing-cross-modal",
    ]
    for req in required_models:
        resolved = runtime.registry.get(req)
        assert resolved is not None, f"Expected model '{req}' to be registered and resolvable in model runtime."


def test_grounding_typed_error_preservation():
    """
    Requirement 11 & 12: Verify that when a specialist model is unavailable,
    ToolExecutor catches ModelUnavailableError and raises an HTTPException with:
    - status_code: 503
    - code: MODEL_UNAVAILABLE
    Never masking it as a generic 500 PlanExecutionError.
    """
    executor = ToolExecutor()

    # Create mock plan for grounding
    plan = WorkflowPlanSchema(
        task="GROUNDING",
        reasoning_summary="Test grounding error preservation",
        steps=[
            PlanStepSchema(
                task="GROUNDING",
                tool="single_image_grounding",
                parameters={"image_id": "00000000-0000-0000-0000-000000000000", "query": "buildings"},
            )
        ]
    )
    trace = ExecutionTrace(original_query="Highlight buildings", input_image_ids=[])

    # Simulate model unavailability inside tool
    tool = executor.registry.get("single_image_grounding")
    assert tool is not None

    async def mock_fail_execute(*args, **kwargs):
        raise ModelUnavailableError("Grounding checkpoint google/owlvit-base-patch32 not found locally.")

    orig_execute = tool.execute
    tool.execute = mock_fail_execute

    import asyncio
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(executor.execute_plan(
            plan=plan,
            input_context={"image_id": "00000000-0000-0000-0000-000000000000", "query": "buildings"},
            trace=trace
        ))

    tool.execute = orig_execute

    assert exc_info.value.status_code == 503
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == "MODEL_UNAVAILABLE"
    assert "google/owlvit-base-patch32" in exc_info.value.detail["message"]


def test_agent_analyze_grounding_end_to_end(client, fixtures_dir: Path):
    """
    Requirement 17: End-to-end agent grounding execution with Demo 2 prompt:
    'Highlight the buildings in this image.'
    Expects:
    - HTTP 200
    - task: GROUNDING
    - tool: single_image_grounding
    - full trace sequence recorded
    """
    sample_png = fixtures_dir / "sample.png"
    if not sample_png.exists():
        pytest.skip("sample.png fixture not available")

    # Ingest image
    files = {"file": ("grounding_test.png", sample_png.read_bytes(), "image/png")}
    upload_res = client.post("/api/v1/images/upload", files=files)
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # Execute Demo 2 agent query
    payload = {
        "query": "Highlight the buildings in this image.",
        "image_ids": [image_id]
    }
    res = client.post("/api/v1/agent/analyze", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "completed"
    assert data["task"] == "GROUNDING"
    assert any(t["name"] == "single_image_grounding" for t in data["tools"])
    assert "regions" in data
    assert "confidence" in data
    assert data["confidence"]["score"] is not None

    # Verify observable trace events
    events = data["trace"]["events"]
    event_types = [ev["event_type"] for ev in events]
    expected_order = [
        "QUERY_RECEIVED",
        "INPUT_VALIDATED",
        "TASK_CLASSIFIED",
        "CAPABILITY_CHECKED",
        "PLAN_GENERATED",
        "TOOL_SELECTED",
        "TOOL_EXECUTED",
        "RESULT_NORMALIZED",
        "FINAL_RESPONSE_GENERATED",
    ]
    for expected in expected_order:
        assert expected in event_types, f"Missing trace event: {expected}"


def test_health_and_readiness_probes(client):
    """
    Requirement 20, 21, 22:
    - /health = liveness probe (HTTP 200, status='ok', database='not_checked', storage='not_checked')
    - /ready = readiness probe (HTTP 200, status='ready', services verified)
    """
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert health_data["database"] == "not_checked"
    assert health_data["storage"] == "not_checked"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data["status"] == "ready"
    assert "services" in ready_data
    assert ready_data["services"]["database"] == "ready"
    assert ready_data["services"]["storage"] == "ready"
    assert "models" in ready_data["services"]
