"""
AgentController for SatQuery AI.
Main orchestration engine interpreting user queries, coordinating classification,
resolving capabilities, compiling safe execution plans, dispatching tools,
and persisting observable traces.
"""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.aggregator import ResultAggregator
from app.agent.classifier import QueryClassifier
from app.agent.exceptions import (
    AmbiguousQueryError,
    CapabilityUnavailableError,
    PlanExecutionError,
)
from app.agent.executor import ToolExecutor
from app.agent.planner import WorkflowPlanner
from app.agent.resolver import CapabilityResolver
from app.agent.schemas import (
    AgentAnalyzeResponse,
    ConfidenceSchema,
    ToolSummarySchema,
)
from app.agent.trace import ExecutionTrace
from app.core.logging import logger
from app.database.models import AgentRunModel, AgentTraceEventModel, BiTemporalPairModel, ImageModel
from app.tools.registry import ToolRegistry, get_tool_registry


class AgentController:
    """
    Central Controller for the SatQuery Agentic Orchestration Layer.
    Ensures safe, bounded execution inside the registered tool sandbox.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()
        self.resolver = CapabilityResolver(self.registry)
        self.planner = WorkflowPlanner(self.registry)
        self.executor = ToolExecutor(self.registry)

    async def analyze(
        self,
        query: str,
        image_ids: Optional[List[uuid.UUID]] = None,
        pair_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> AgentAnalyzeResponse:
        """
        Executes end-to-end agentic workflow:
        Query -> Normalize -> Classify -> Capability Check -> Plan -> Execute -> Aggregate -> Trace -> Persist.
        """
        run_id = uuid.uuid4()

        # If pair_id is provided and image_ids is empty, lookup pair in DB
        if pair_id and not image_ids and db:
            pair_stmt = select(BiTemporalPairModel).where(BiTemporalPairModel.id == pair_id)
            pair_res = await db.execute(pair_stmt)
            pair_record = pair_res.scalar_one_or_none()
            if not pair_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bi-temporal pair '{pair_id}' not found in registry."
                )
            image_ids = [pair_record.image_t1_id, pair_record.image_t2_id]

        if not image_ids and not pair_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one satellite image ID or a bi-temporal pair_id must be provided."
            )

        image_ids = image_ids or []
        image_str_ids = [str(img_id) for img_id in image_ids]
        trace = ExecutionTrace(
            original_query=query,
            input_image_ids=image_str_ids,
            trace_id=run_id
        )

        start_perf = time.perf_counter()

        # Step 1: QUERY_RECEIVED
        trace.add_event(
            event_type="QUERY_RECEIVED",
            status="completed",
            output_metadata={
                "query_length": len(query),
                "image_count": len(image_ids),
                "pair_id": str(pair_id) if pair_id else None,
            }
        )

        # Step 2: INPUT_VALIDATED (Fetch satellite images from database)
        input_context: Dict[str, Any] = {
            "image_ids": image_str_ids,
            "number_of_images": len(image_ids),
            "pair_id": str(pair_id) if pair_id else None,
            "images": []
        }

        if db and image_ids:
            stmt = select(ImageModel).where(ImageModel.id.in_(image_ids))
            res = await db.execute(stmt)
            db_images = res.scalars().all()

            if not db_images:
                err_msg = f"None of the provided image IDs were found in the image registry."
                trace.add_event("INPUT_VALIDATED", status="failed", output_metadata={"error": err_msg})
                trace.finish(status="failed", error=err_msg)
                await self._persist_run(trace, run_id, "failed", err_msg, db)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)

            # Preserve ordering of image_ids (e.g. T1 before T2)
            img_map = {img.id: img for img in db_images}
            images = [img_map[img_id] for img_id in image_ids if img_id in img_map]

            for img in images:
                input_context["images"].append({
                    "id": str(img.id),
                    "modality": img.modality,
                    "is_geospatial": img.is_geospatial,
                    "width": img.width,
                    "height": img.height,
                    "band_count": img.band_count,
                    "crs": img.crs,
                })

            primary_img = images[0]
            input_context["modality"] = primary_img.modality
            input_context["image_id"] = str(primary_img.id)

            trace.add_event(
                event_type="INPUT_VALIDATED",
                status="completed",
                output_metadata={
                    "verified_images": len(images),
                    "primary_modality": primary_img.modality,
                    "is_geospatial": primary_img.is_geospatial,
                    "pair_id": str(pair_id) if pair_id else None,
                }
            )
        else:
            # Fallback for headless testing
            input_context["modality"] = "optical"
            if image_str_ids:
                input_context["image_id"] = image_str_ids[0]
            trace.add_event("INPUT_VALIDATED", status="completed", output_metadata={"verified_images": len(image_ids)})

        # Step 3: TASK_CLASSIFIED (Query Normalization + Intent Classification)
        classification = QueryClassifier.classify(query, input_context)
        trace.normalized_query = classification.normalized_query
        trace.detected_task = classification.intent
        trace.task_confidence = classification.confidence

        trace.add_event(
            event_type="TASK_CLASSIFIED",
            status="completed",
            output_metadata={
                "detected_task": classification.intent,
                "confidence": classification.confidence,
                "reasoning_summary": classification.reasoning_summary,
                "is_ambiguous": classification.is_ambiguous
            }
        )

        total_elapsed = int((time.perf_counter() - start_perf) * 1000)

        # Step 4: Handle Ambiguous Queries (Do not guess when ambiguity is high)
        if classification.is_ambiguous:
            clarification = classification.clarification_prompt or "Would you like a scene description or an answer to a specific question?"
            trace.finish(status="ambiguous")
            await self._persist_run(
                trace=trace,
                run_id=run_id,
                status="ambiguous",
                answer=clarification,
                error=None,
                db=db
            )
            return AgentAnalyzeResponse(
                analysis_id=None,
                status="ambiguous",
                task=classification.intent,
                answer=clarification,
                confidence=ConfidenceSchema(score=classification.confidence, method="ambiguity_threshold"),
                tools=[],
                trace_id=trace.trace_id,
                trace=trace.to_schema(),
                clarification_needed=clarification,
                processing_time_ms=total_elapsed
            )

        # Step 5: CAPABILITY_CHECKED (Inspect Capability Matrix)
        resolution = self.resolver.resolve(classification.intent, input_context)
        trace.add_event(
            event_type="CAPABILITY_CHECKED",
            status="completed" if resolution.is_executable else "unsupported",
            output_metadata={
                "task": resolution.task,
                "is_executable": resolution.is_executable,
                "phase_availability": resolution.phase_availability,
                "status_reason": resolution.status_reason
            }
        )

        # Step 6: Handle Unsupported Future Capabilities (Do NOT fall back to VQA!)
        if not resolution.is_executable:
            trace.finish(status="unavailable")
            unavailable_message = (
                f"This analysis capability is not available yet. {resolution.status_reason}"
            )
            await self._persist_run(
                trace=trace,
                run_id=run_id,
                status="unavailable",
                answer=unavailable_message,
                error=None,
                db=db
            )
            return AgentAnalyzeResponse(
                analysis_id=None,
                status="unavailable",
                task=resolution.task,
                answer=unavailable_message,
                confidence=ConfidenceSchema(score=classification.confidence, method="capability_resolution"),
                tools=[
                    ToolSummarySchema(
                        name=resolution.task.lower(),
                        version="planned",
                        task=resolution.task,
                        status="planned",
                        description=resolution.status_reason
                    )
                ],
                trace_id=trace.trace_id,
                trace=trace.to_schema(),
                clarification_needed=None,
                processing_time_ms=total_elapsed
            )

        # Step 7: PLAN_GENERATED (Structured Execution Plan)
        assert resolution.tool is not None
        plan = self.planner.create_plan(
            task=resolution.task,
            tool=resolution.tool,
            query=classification.normalized_query,
            input_context=input_context
        )
        trace.selected_tools = [s.tool for s in plan.steps]
        trace.tool_parameters = plan.steps[0].parameters if plan.steps else {}

        trace.add_event(
            event_type="PLAN_GENERATED",
            status="completed",
            output_metadata={
                "step_count": len(plan.steps),
                "planned_tools": trace.selected_tools,
                "summary": plan.reasoning_summary
            }
        )

        # Step 8: TOOL_EXECUTED (Safe Sandboxed Execution)
        try:
            tool_outputs = await self.executor.execute_plan(
                plan=plan,
                input_context=input_context,
                trace=trace,
                db=db
            )
        except Exception as e:
            err_msg = str(e.detail.get("message", e.detail) if isinstance(getattr(e, "detail", None), dict) else (getattr(e, "detail", None) or str(e)))
            trace.finish(status="failed", error=err_msg)
            await self._persist_run(trace, run_id, "failed", error=err_msg, db=db)
            raise

        # Step 9: RESULT_NORMALIZED
        aggregated = ResultAggregator.aggregate(resolution.task, tool_outputs)
        trace.analysis_id = aggregated["analysis_id"]
        trace.tool_outputs = {"answer": aggregated["answer"], "confidence": aggregated["confidence"].score}

        trace.add_event(
            event_type="RESULT_NORMALIZED",
            status="completed",
            output_metadata={
                "analysis_id": str(aggregated["analysis_id"]) if aggregated["analysis_id"] else None,
                "confidence_score": aggregated["confidence"].score,
                "confidence_method": aggregated["confidence"].method
            }
        )

        # Step 10: FINAL_RESPONSE_GENERATED
        trace.add_event(
            event_type="FINAL_RESPONSE_GENERATED",
            status="completed",
            output_metadata={"final_task": resolution.task}
        )

        trace.finish(status="completed")
        total_elapsed = trace.total_duration_ms

        await self._persist_run(
            trace=trace,
            run_id=run_id,
            status="completed",
            answer=aggregated["answer"],
            confidence_score=aggregated["confidence"].score,
            confidence_method=aggregated["confidence"].method,
            analysis_id=aggregated["analysis_id"],
            plan_json=plan.model_dump(),
            db=db
        )

        return AgentAnalyzeResponse(
            analysis_id=aggregated["analysis_id"],
            pair_id=aggregated.get("pair_id") or pair_id,
            status="completed",
            task=resolution.task,
            answer=aggregated["answer"],
            confidence=aggregated["confidence"],
            tools=aggregated["tools"],
            evidence=aggregated.get("evidence", []),
            regions=aggregated.get("regions", []),
            change_metrics=aggregated.get("change_metrics"),
            artifact_key=aggregated.get("artifact_key"),
            trace_id=trace.trace_id,
            trace=trace.to_schema(),
            clarification_needed=None,
            processing_time_ms=total_elapsed,
            is_adapted=aggregated.get("is_adapted", False),
            adapter_id=aggregated.get("adapter_id"),
            fallback_used=aggregated.get("fallback_used", False),
            fallback_reason=aggregated.get("fallback_reason"),
            observations=aggregated.get("observations"),
        )

    async def _persist_run(
        self,
        trace: ExecutionTrace,
        run_id: uuid.UUID,
        status: str,
        answer: Optional[str] = None,
        confidence_score: Optional[float] = None,
        confidence_method: Optional[str] = None,
        analysis_id: Optional[uuid.UUID] = None,
        plan_json: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """Persists AgentRunModel and AgentTraceEventModel records to SQLite."""
        if not db:
            return

        try:
            run_record = AgentRunModel(
                id=run_id,
                analysis_id=analysis_id,
                original_query=trace.original_query,
                normalized_query=trace.normalized_query,
                detected_task=trace.detected_task,
                classification_confidence=trace.task_confidence,
                selected_tools=trace.selected_tools,
                plan_json=plan_json,
                status=status,
                answer=answer,
                confidence_score=confidence_score,
                confidence_method=confidence_method,
                error=error,
                started_at=trace.started_at,
                completed_at=trace.completed_at or datetime.datetime.now(datetime.timezone.utc),
                duration_ms=trace.total_duration_ms,
            )
            db.add(run_record)
            await db.flush()

            for ev in trace.events:
                event_record = AgentTraceEventModel(
                    agent_run_id=run_id,
                    sequence=ev["sequence"],
                    event_type=ev["event_type"],
                    tool_name=ev.get("tool_name"),
                    status=ev.get("status", "completed"),
                    parameters_json=ev.get("parameters"),
                    output_metadata_json=ev.get("output_metadata"),
                    duration_ms=ev.get("duration_ms"),
                    timestamp=ev.get("timestamp", datetime.datetime.now(datetime.timezone.utc)),
                )
                db.add(event_record)

            await db.flush()
            logger.info(f"Persisted agent run '{run_id}' with {len(trace.events)} trace events.")
        except Exception as e:
            logger.warning(f"Failed to persist agent run '{run_id}' to DB: {e}")
