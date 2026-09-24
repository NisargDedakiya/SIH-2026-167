"""
Unit and Integration tests for SatQuery Agentic Orchestration Layer (Phase 3).
Verifies query normalization, hybrid intent classification, capability resolution,
parameter validation, sandboxed tool dispatch, execution trace generation, and API endpoints.
"""

import io
import uuid
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient

from app.agent.aggregator import ResultAggregator
from app.agent.classifier import QueryClassifier, QueryNormalizer
from app.agent.controller import AgentController
from app.agent.exceptions import ParameterValidationError
from app.agent.executor import ToolExecutor
from app.agent.planner import WorkflowPlanner
from app.agent.resolver import CapabilityResolver
from app.agent.trace import ExecutionTrace
from app.tools.base import AnalysisTool
from app.tools.registry import ToolRegistry, get_tool_registry
from app.tools.vqa import SingleImageVQATool
from app.tools.caption import SingleImageCaptionTool


def create_synthetic_geotiff_bytes() -> bytes:
    mem_buffer = io.BytesIO()
    data = (np.random.rand(3, 64, 64) * 4000).astype(np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)
    with rasterio.open(
        mem_buffer,
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)
    return mem_buffer.getvalue()


# =========================================================================
# 1. Query Normalization Tests
# =========================================================================

def test_query_normalization():
    assert QueryNormalizer.normalize("  What type of land   cover? \n\t") == "What type of land cover?"
    assert QueryNormalizer.normalize("") == ""
    assert QueryNormalizer.normalize("Describe    scene   ") == "Describe scene"


# =========================================================================
# 2. Required 6 Agent Test Cases
# =========================================================================

def test_agent_required_case_1_vqa():
    """Test 1: 'What type of land cover is visible?' -> VISUAL_QUESTION_ANSWERING -> single_image_vqa"""
    q = "What type of land cover is visible?"
    res = QueryClassifier.classify(q)
    assert res.intent == "VISUAL_QUESTION_ANSWERING"
    assert res.confidence >= 0.85
    assert not res.is_ambiguous

    resolver = CapabilityResolver()
    compat = resolver.resolve(res.intent, {"number_of_images": 1})
    assert compat.is_executable is True
    assert compat.tool is not None
    assert compat.tool.name == "single_image_vqa"


def test_agent_required_case_2_caption():
    """Test 2: 'Describe this scene.' -> SCENE_DESCRIPTION -> single_image_caption"""
    q = "Describe this scene."
    res = QueryClassifier.classify(q)
    assert res.intent == "SCENE_DESCRIPTION"
    assert res.confidence >= 0.85
    assert not res.is_ambiguous

    resolver = CapabilityResolver()
    compat = resolver.resolve(res.intent, {"number_of_images": 1})
    assert compat.is_executable is True
    assert compat.tool is not None
    assert compat.tool.name == "single_image_caption"


def test_agent_required_case_3_grounding():
    """Test 3: 'Highlight the water body.' -> GROUNDING -> single_image_grounding (Phase 4 active)"""
    q = "Highlight the water body."
    res = QueryClassifier.classify(q)
    assert res.intent == "GROUNDING"
    assert not res.is_ambiguous

    resolver = CapabilityResolver()
    compat = resolver.resolve(res.intent, {"number_of_images": 1})
    assert compat.is_executable is True
    assert compat.tool is not None
    assert compat.tool.name == "single_image_grounding"


def test_agent_required_case_4_change_analysis():
    """Test 4: 'What changed between these two dates?' -> CHANGE_ANALYSIS -> now executable in Phase 5"""
    q = "What changed between these two dates?"
    res = QueryClassifier.classify(q)
    assert res.intent == "CHANGE_ANALYSIS"
    assert not res.is_ambiguous

    resolver = CapabilityResolver()
    compat = resolver.resolve(res.intent, {"number_of_images": 2})
    assert compat.is_executable is True
    assert compat.tool is not None
    assert "change" in compat.tool.name


def test_agent_required_case_5_cross_modal():
    """Test 5: 'Use the optical and SAR images together.' -> CROSS_MODAL_ANALYSIS -> active in Phase 6"""
    q = "Use the optical and SAR images together."
    res = QueryClassifier.classify(q)
    assert res.intent == "CROSS_MODAL_ANALYSIS"
    assert not res.is_ambiguous

    resolver = CapabilityResolver()
    compat = resolver.resolve(res.intent, {"number_of_images": 2})
    assert compat.is_executable is True
    assert "Phase 6" in compat.phase_availability
    assert compat.tool is not None
    assert compat.tool.name == "optical_sar_analysis"


def test_agent_required_case_6_ambiguous():
    """Test 6: 'Tell me about this.' -> ambiguous -> ask clarification"""
    q = "Tell me about this."
    res = QueryClassifier.classify(q)
    assert res.intent == "AMBIGUOUS"
    assert res.is_ambiguous is True
    assert res.clarification_prompt is not None
    assert "clarification" in res.clarification_prompt.lower() or "scene description" in res.clarification_prompt.lower()


# =========================================================================
# 3. Tool Registry & Capability Tests
# =========================================================================

def test_tool_registry_enumeration():
    reg = get_tool_registry()
    tools = reg.list()
    names = [t.name for t in tools]

    assert "single_image_vqa" in names
    assert "single_image_caption" in names
    assert "single_image_grounding" in names
    assert "bi_temporal_change_detection" in names
    assert "optical_sar_analysis" in names
    assert "optical_sar_vqa" in names
    assert "optical_sar_grounding" in names

    # Check available
    avail = [t.name for t in reg.list_available()]
    assert "single_image_vqa" in avail
    assert "single_image_caption" in avail
    assert "single_image_grounding" in avail
    assert "bi_temporal_change_detection" in avail
    assert "optical_sar_analysis" in avail
    assert "optical_sar_vqa" in avail
    assert "optical_sar_grounding" in avail




def test_planner_parameter_validation():
    planner = WorkflowPlanner()
    tool = SingleImageVQATool()

    # Valid plan
    plan = planner.create_plan(
        task="VISUAL_QUESTION_ANSWERING",
        tool=tool,
        query="What is the terrain?",
        input_context={"image_ids": [str(uuid.uuid4())], "modality": "optical"}
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].parameters["query"] == "What is the terrain?"

    # Missing query for VQA should fail validation
    with pytest.raises(ParameterValidationError):
        planner.create_plan(
            task="VISUAL_QUESTION_ANSWERING",
            tool=tool,
            query="",
            input_context={"image_ids": [str(uuid.uuid4())]}
        )


# =========================================================================
# 4. Result Aggregator & Trace Tests
# =========================================================================

def test_result_aggregator_normalization():
    mock_tool_output = {
        "analysis_id": str(uuid.uuid4()),
        "status": "completed",
        "task": "VISUAL_QUESTION_ANSWERING",
        "tool_name": "single_image_vqa",
        "tool_version": "1.0.0",
        "answer": "Dense vegetation with river tributary.",
        "confidence": {"score": 0.88, "method": "token_probability"},
        "evidence": [{"type": "bbox", "coords": [10, 10, 50, 50]}],
        "processing_time_ms": 120
    }

    res = ResultAggregator.aggregate("VISUAL_QUESTION_ANSWERING", [mock_tool_output])
    assert res["answer"] == "Dense vegetation with river tributary."
    assert res["confidence"].score == 0.88
    assert res["confidence"].method == "token_probability"
    assert len(res["tools"]) == 1
    assert res["tools"][0].name == "single_image_vqa"


def test_execution_trace_events():
    trace = ExecutionTrace("Describe this scene.", ["img-123"])
    trace.add_event("QUERY_RECEIVED", status="completed")
    trace.add_event("INPUT_VALIDATED", status="completed")
    trace.add_event("TASK_CLASSIFIED", status="completed", output_metadata={"intent": "SCENE_DESCRIPTION"})
    trace.add_event("TOOL_SELECTED", tool_name="single_image_caption", status="completed")
    trace.finish(status="completed")

    schema = trace.to_schema()
    assert len(schema.events) == 4
    assert schema.events[0].event_type == "QUERY_RECEIVED"
    assert schema.events[2].event_type == "TASK_CLASSIFIED"
    assert schema.tool_status == "completed"
    assert schema.total_duration_ms >= 0


# =========================================================================
# 5. Integration Tests: API Endpoints (POST /analyze, GET /tools, GET /runs)
# =========================================================================

def test_agent_api_tools_list(client: TestClient):
    """GET /api/v1/agent/tools returns registered tools."""
    resp = client.get("/api/v1/agent/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    names = [t["name"] for t in data]
    assert "single_image_vqa" in names
    assert "single_image_caption" in names
    assert "single_image_grounding" in names


def test_agent_api_vqa_query_end_to_end(client: TestClient):
    """POST /api/v1/agent/analyze with VQA query."""
    # 1. Upload an image
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_agent_vqa.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    # 2. Call Agent with Question
    agent_res = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "What type of land cover is visible in this image?",
            "image_ids": [image_id]
        }
    )
    assert agent_res.status_code == 200
    data = agent_res.json()

    assert data["status"] == "completed"
    assert data["task"] == "VISUAL_QUESTION_ANSWERING"
    assert "agricultural" in data["answer"].lower() or len(data["answer"]) > 5
    assert data["confidence"]["score"] > 0.7
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "single_image_vqa"
    assert data["trace_id"] is not None

    # Verify execution trace
    trace = data["trace"]
    assert trace is not None
    assert trace["detected_task"] == "VISUAL_QUESTION_ANSWERING"
    assert len(trace["events"]) >= 5
    event_types = [e["event_type"] for e in trace["events"]]
    assert "QUERY_RECEIVED" in event_types
    assert "TASK_CLASSIFIED" in event_types
    assert "TOOL_SELECTED" in event_types
    assert "TOOL_EXECUTED" in event_types


def test_agent_api_caption_query_end_to_end(client: TestClient):
    """POST /api/v1/agent/analyze with Caption query."""
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_agent_cap.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    agent_res = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "Describe this scene.",
            "image_ids": [image_id]
        }
    )
    assert agent_res.status_code == 200
    data = agent_res.json()

    assert data["status"] == "completed"
    assert data["task"] == "SCENE_DESCRIPTION"
    assert len(data["answer"]) > 10
    assert data["confidence"]["score"] > 0.7
    assert data["tools"][0]["name"] == "single_image_caption"


def test_agent_api_unsupported_capability_no_fallback(client: TestClient):
    """POST /api/v1/agent/analyze with Change Analysis query -> unavailable, NO VQA fallback."""
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_agent_change.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    agent_res = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "What changed between these two images?",
            "image_ids": [image_id]
        }
    )
    assert agent_res.status_code == 200
    data = agent_res.json()

    assert data["status"] == "unavailable"
    assert data["task"] == "CHANGE_ANALYSIS"
    assert "not available yet" in data["answer"].lower()
    # Must NOT run VQA!
    assert data["tools"][0]["name"] != "single_image_vqa"


def test_agent_api_ambiguous_query_handling(client: TestClient):
    """POST /api/v1/agent/analyze with 'Tell me about this.' -> ambiguous status with clarification prompt."""
    geo_bytes = create_synthetic_geotiff_bytes()
    upload_res = client.post(
        "/api/v1/images/upload",
        files={"file": ("test_agent_ambig.tif", geo_bytes, "image/tiff")}
    )
    assert upload_res.status_code == 201
    image_id = upload_res.json()["id"]

    agent_res = client.post(
        "/api/v1/agent/analyze",
        json={
            "query": "Tell me about this.",
            "image_ids": [image_id]
        }
    )
    assert agent_res.status_code == 200
    data = agent_res.json()

    assert data["status"] == "ambiguous"
    assert data["clarification_needed"] is not None
    assert "clarification" in data["clarification_needed"].lower() or "scene description" in data["clarification_needed"].lower()
