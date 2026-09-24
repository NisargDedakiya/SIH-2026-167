"""
API Endpoints for SatQuery Agentic Orchestrator and Tool Registry.
"""

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.controller import AgentController
from app.agent.schemas import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    ToolSummarySchema,
)
from app.database.models import AgentRunModel, AgentTraceEventModel
from app.database.session import get_db
from app.tools.registry import get_tool_registry

router = APIRouter()
_controller = AgentController()


@router.post("/analyze", response_model=AgentAnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_with_agent(
    request: AgentAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Primary Agentic Query Endpoint.
    Interprets natural-language queries, determines tasks, selects registered specialist tools,
    executes workflows safely, and returns answers with complete execution traces.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User query string cannot be empty."
        )

    if not request.image_ids and not request.pair_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one satellite image ID or a bi-temporal pair_id must be provided."
        )

    return await _controller.analyze(
        query=request.query,
        image_ids=request.image_ids,
        pair_id=request.pair_id,
        db=db
    )


@router.get("/tools", response_model=List[ToolSummarySchema])
async def list_agent_tools():
    """
    Enumerate all registered analytical tools and future capability placeholders
    managed by the SatQuery ToolRegistry.
    """
    registry = get_tool_registry()
    tools = registry.list()
    return [
        ToolSummarySchema(
            name=tool.name,
            version=tool.version,
            task=tool.task,
            status=tool.status,
            description=tool.description
        )
        for tool in tools
    ]


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_agent_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve persisted execution record and observable trace events for an Agent run.
    """
    stmt = (
        select(AgentRunModel)
        .options(selectinload(AgentRunModel.trace_events))
        .where(AgentRunModel.id == run_id)
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent run '{run_id}' not found."
        )

    return {
        "id": record.id,
        "analysis_id": record.analysis_id,
        "original_query": record.original_query,
        "normalized_query": record.normalized_query,
        "detected_task": record.detected_task,
        "classification_confidence": record.classification_confidence,
        "selected_tools": record.selected_tools,
        "plan": record.plan_json,
        "status": record.status,
        "answer": record.answer,
        "confidence_score": record.confidence_score,
        "confidence_method": record.confidence_method,
        "error": record.error,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "duration_ms": record.duration_ms,
        "trace_events": [
            {
                "sequence": ev.sequence,
                "event_type": ev.event_type,
                "tool_name": ev.tool_name,
                "status": ev.status,
                "parameters": ev.parameters_json,
                "output_metadata": ev.output_metadata_json,
                "duration_ms": ev.duration_ms,
                "timestamp": ev.timestamp,
            }
            for ev in record.trace_events
        ]
    }
