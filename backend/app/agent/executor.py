"""
Tool Executor for SatQuery AI.
Safely executes planned tools within strict sandboxed parameter boundaries.
Captures timing, errors, and observable outputs for the execution trace.
"""

import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status
from app.agent.exceptions import PlanExecutionError
from app.agent.schemas import WorkflowPlanSchema
from app.agent.trace import ExecutionTrace
from app.ai.exceptions import AIError, InferenceError, ModelUnavailableError, UnsupportedModalityError
from app.core.logging import logger
from app.tools.registry import ToolRegistry, get_tool_registry


class ToolExecutor:
    """
    Sandboxed Tool Execution Engine.
    Strictly forbids dynamic code/shell execution.
    Executes only pre-registered AnalysisTool instances and records fine-grained events.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()

    async def execute_plan(
        self,
        plan: WorkflowPlanSchema,
        input_context: Dict[str, Any],
        trace: ExecutionTrace,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes all steps in the plan sequentially and records observable trace events.
        """
        results: List[Dict[str, Any]] = []

        for idx, step in enumerate(plan.steps):
            tool = self.registry.get(step.tool)
            if not tool or tool.status != "available":
                err_msg = f"Security Violation: Attempted execution of unregistered/unavailable tool '{step.tool}'."
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=step.tool,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": err_msg}
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "TOOL_NOT_FOUND",
                        "message": err_msg,
                        "details": {"tool": step.tool}
                    }
                )

            # Record tool start
            trace.add_event(
                event_type="TOOL_SELECTED",
                tool_name=tool.name,
                status="started",
                parameters=step.parameters,
                output_metadata={
                    "tool_version": tool.version,
                    "task": step.task
                }
            )

            step_start = time.perf_counter()
            try:
                # Execute tool
                tool_output = await tool.execute(
                    input_context=input_context,
                    parameters=step.parameters,
                    db=db
                )
                duration_ms = int((time.perf_counter() - step_start) * 1000)

                # Record observable completion fact
                conf_val = tool_output.get("confidence")
                conf_score = None
                if isinstance(conf_val, dict):
                    conf_score = conf_val.get("score")
                elif isinstance(conf_val, (float, int)):
                    conf_score = float(conf_val)

                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="completed",
                    parameters=step.parameters,
                    output_metadata={
                        "analysis_id": str(tool_output.get("analysis_id")) if tool_output.get("analysis_id") else None,
                        "model": tool_output.get("model"),
                        "is_adapted": tool_output.get("is_adapted", False),
                        "adapter": "satquery-rs-v1" if tool_output.get("is_adapted") else None,
                        "fallback": tool_output.get("fallback"),
                        "confidence": conf_score,
                        "processing_time_ms": duration_ms,
                    },
                    duration_ms=duration_ms
                )

                if "tool_name" not in tool_output:
                    tool_output["tool_name"] = tool.name
                if "tool_version" not in tool_output:
                    tool_output["tool_version"] = tool.version
                if "description" not in tool_output:
                    tool_output["description"] = tool.description

                results.append(tool_output)

            except HTTPException as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                err_detail = e.detail if isinstance(e.detail, str) else str(e.detail.get("message", e.detail) if isinstance(e.detail, dict) else e.detail)
                logger.warning(f"HTTPException on tool '{tool.name}': {e.status_code} - {err_detail}")
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": err_detail, "status_code": e.status_code},
                    duration_ms=duration_ms
                )
                raise
            except ModelUnavailableError as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Model unavailable on tool '{tool.name}': {e}")
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e), "code": "MODEL_UNAVAILABLE"},
                    duration_ms=duration_ms
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "code": "MODEL_UNAVAILABLE",
                        "message": f"Specialist model for tool '{tool.name}' is unavailable: {str(e)}",
                        "details": {"tool": tool.name, "task": step.task}
                    }
                ) from e
            except UnsupportedModalityError as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Unsupported modality on tool '{tool.name}': {e}")
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e), "code": "UNSUPPORTED_MODALITY"},
                    duration_ms=duration_ms
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "UNSUPPORTED_MODALITY",
                        "message": str(e),
                        "details": {"tool": tool.name}
                    }
                ) from e
            except InferenceError as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Inference error on tool '{tool.name}': {e}", exc_info=True)
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e), "code": "MODEL_EXECUTION_FAILURE"},
                    duration_ms=duration_ms
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "code": "MODEL_EXECUTION_FAILURE",
                        "message": f"Inference execution failed on tool '{tool.name}': {str(e)}",
                        "details": {"tool": tool.name}
                    }
                ) from e
            except PlanExecutionError as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Plan execution error on tool '{tool.name}': {e}")
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e), "code": "TOOL_EXECUTION_FAILURE"},
                    duration_ms=duration_ms
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "code": "TOOL_EXECUTION_FAILURE",
                        "message": str(e),
                        "details": {"tool": tool.name}
                    }
                ) from e
            except Exception as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Unexpected execution failure on tool '{tool.name}': {e}", exc_info=True)
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e), "code": "INTERNAL_ERROR"},
                    duration_ms=duration_ms
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "code": "INTERNAL_ERROR",
                        "message": f"Tool '{tool.name}' encountered an unexpected failure: {str(e)}",
                        "details": {"tool": tool.name}
                    }
                ) from e

        return results
