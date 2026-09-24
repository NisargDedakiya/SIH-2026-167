"""
Workflow Planner for SatQuery AI.
Produces structured, deterministic execution plans composed exclusively of registered tools
with strictly validated parameter sets.
"""

from typing import Any, Dict, List, Optional

from app.agent.exceptions import ParameterValidationError, PlanExecutionError
from app.agent.schemas import PlanStepSchema, WorkflowPlanSchema
from app.tools.base import AnalysisTool
from app.tools.registry import ToolRegistry, get_tool_registry


class WorkflowPlanner:
    """
    Constructs deterministic execution plans from resolved capabilities.
    Validates input schemas before plan issuance to prevent runtime parameter poisoning.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()

    def create_plan(
        self,
        task: str,
        tool: AnalysisTool,
        query: str,
        input_context: Dict[str, Any]
    ) -> WorkflowPlanSchema:
        """
        Builds a verified workflow plan for the given task and tool.
        """
        # 1. Enforce that tool exists in registry
        reg_tool = self.registry.get(tool.name)
        if not reg_tool or reg_tool.status != "available":
            raise PlanExecutionError(f"Cannot plan unverified or unavailable tool: '{tool.name}'.")

        # 2. Extract and validate required inputs
        image_ids = input_context.get("image_ids", [])
        if not image_ids and "image_id" in input_context:
            image_ids = [input_context["image_id"]]
        pair_id = input_context.get("pair_id")

        if task == "CHANGE_ANALYSIS":
            if not pair_id and len(image_ids) < 2:
                raise ParameterValidationError(
                    "CHANGE_ANALYSIS requires either a registered 'pair_id' or at least 2 satellite image IDs (T1 and T2)."
                )
            params: Dict[str, Any] = {}
            if pair_id:
                params["pair_id"] = str(pair_id)
            if len(image_ids) >= 2:
                params["t1_image_id"] = str(image_ids[0])
                params["t2_image_id"] = str(image_ids[1])
            if query and query.strip():
                params["query"] = query.strip()
        elif task == "CROSS_MODAL_ANALYSIS":
            if not pair_id and len(image_ids) < 2:
                raise ParameterValidationError(
                    "CROSS_MODAL_ANALYSIS requires either a registered 'pair_id' or at least 2 satellite image IDs (Optical and SAR)."
                )
            params: Dict[str, Any] = {}
            if pair_id:
                params["pair_id"] = str(pair_id)
            if len(image_ids) >= 2:
                params["optical_image_id"] = str(image_ids[0])
                params["sar_image_id"] = str(image_ids[1])
            if query and query.strip():
                params["query"] = query.strip()
        else:
            if not image_ids:
                raise ParameterValidationError("No valid satellite image ID provided for execution plan.")

            primary_image_id = str(image_ids[0])

            # 3. Construct bounded, explicit parameters
            params: Dict[str, Any] = {
                "image_id": primary_image_id
            }

            if task in ["VISUAL_QUESTION_ANSWERING", "GROUNDING"]:
                if not query or not query.strip():
                    raise ParameterValidationError(f"A non-empty query expression is required for {task}.")
                params["query"] = query.strip()

        # 4. Perform tool-level pre-validation
        tool.validate_inputs(input_context, params)

        step = PlanStepSchema(
            tool=tool.name,
            task=task,
            parameters=params
        )

        return WorkflowPlanSchema(
            task=task,
            steps=[step],
            reasoning_summary=f"Dispatched single-stage workflow to specialist tool '{tool.name}' (v{tool.version})."
        )
