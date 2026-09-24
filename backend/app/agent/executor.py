"""
Tool Executor for SatQuery AI.
Safely executes planned tools within strict sandboxed parameter boundaries.
Captures timing, errors, and observable outputs for the execution trace.
"""

import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.exceptions import PlanExecutionError
from app.agent.schemas import WorkflowPlanSchema
from app.agent.trace import ExecutionTrace
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
                raise PlanExecutionError(err_msg)

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

            except Exception as e:
                duration_ms = int((time.perf_counter() - step_start) * 1000)
                logger.error(f"Execution failed on tool '{tool.name}': {e}", exc_info=True)
                trace.add_event(
                    event_type="TOOL_EXECUTED",
                    tool_name=tool.name,
                    status="failed",
                    parameters=step.parameters,
                    output_metadata={"error": str(e)},
                    duration_ms=duration_ms
                )
                raise PlanExecutionError(f"Tool '{tool.name}' failed during execution: {str(e)}") from e

        return results
