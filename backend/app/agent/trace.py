"""
Execution Trace recorder for SatQuery Agentic Orchestration.
Captures observable execution facts for SIH auditability and UI inspection.
Guarantees NO hidden chain-of-thought is captured or leaked.
"""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional

from app.agent.schemas import ExecutionTraceSchema, TraceEventSchema


class ExecutionTrace:
    """
    In-memory collector for an Agent run's lifecycle trace.
    Maintains chronological sequence of observable events and timing metrics.
    """

    def __init__(
        self,
        original_query: str,
        input_image_ids: List[str],
        trace_id: Optional[uuid.UUID] = None
    ):
        self.trace_id = trace_id or uuid.uuid4()
        self.analysis_id: Optional[uuid.UUID] = None
        self.started_at = datetime.datetime.now(datetime.timezone.utc)
        self.completed_at: Optional[datetime.datetime] = None
        self._start_perf = time.perf_counter()

        self.original_query = original_query
        self.normalized_query = original_query.strip()
        self.detected_task = "UNKNOWN"
        self.task_confidence = 0.0
        self.input_image_ids = input_image_ids
        self.selected_tools: List[str] = []
        self.tool_parameters: Dict[str, Any] = {}
        self.tool_status = "pending"
        self.tool_outputs: Optional[Dict[str, Any]] = None
        self.errors: List[str] = []

        self.events: List[Dict[str, Any]] = []
        self._sequence_counter = 0

    def add_event(
        self,
        event_type: str,
        tool_name: Optional[str] = None,
        status: str = "completed",
        parameters: Optional[Dict[str, Any]] = None,
        output_metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Appends an observable execution fact event to the trace.
        Filters out any potential sensitive or non-observable internal states.
        """
        self._sequence_counter += 1
        event = {
            "sequence": self._sequence_counter,
            "event_type": event_type,
            "tool_name": tool_name,
            "status": status,
            "parameters": self._sanitize_dict(parameters) if parameters else None,
            "output_metadata": self._sanitize_dict(output_metadata) if output_metadata else None,
            "duration_ms": duration_ms,
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
        }
        self.events.append(event)

    def finish(self, status: str = "completed", error: Optional[str] = None) -> None:
        """Marks trace as complete and calculates total duration."""
        self.completed_at = datetime.datetime.now(datetime.timezone.utc)
        self.tool_status = status
        if error:
            self.errors.append(error)

    @property
    def total_duration_ms(self) -> int:
        return int((time.perf_counter() - self._start_perf) * 1000)

    @staticmethod
    def _sanitize_dict(d: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Ensures dictionaries only contain JSON-serializable, non-private data."""
        if not d:
            return {}
        sanitized = {}
        for k, v in d.items():
            if k.startswith("_") or "prompt" in k.lower() or "chain_of_thought" in k.lower():
                continue
            if isinstance(v, uuid.UUID):
                sanitized[k] = str(v)
            elif isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                sanitized[k] = v
            else:
                sanitized[k] = str(v)
        return sanitized

    def to_schema(self) -> ExecutionTraceSchema:
        """Converts collector state to Pydantic ExecutionTraceSchema."""
        events_schema = [
            TraceEventSchema(
                sequence=ev["sequence"],
                event_type=ev["event_type"],
                tool_name=ev["tool_name"],
                status=ev["status"],
                parameters=ev["parameters"],
                output_metadata=ev["output_metadata"],
                duration_ms=ev["duration_ms"],
                timestamp=ev["timestamp"]
            )
            for ev in self.events
        ]

        return ExecutionTraceSchema(
            trace_id=self.trace_id,
            analysis_id=self.analysis_id,
            started_at=self.started_at,
            completed_at=self.completed_at or datetime.datetime.now(datetime.timezone.utc),
            original_query=self.original_query,
            normalized_query=self.normalized_query,
            detected_task=self.detected_task,
            task_confidence=self.task_confidence,
            input_image_ids=self.input_image_ids,
            selected_tools=self.selected_tools,
            tool_parameters=self._sanitize_dict(self.tool_parameters),
            tool_status=self.tool_status,
            tool_outputs=self._sanitize_dict(self.tool_outputs),
            errors=self.errors,
            total_duration_ms=self.total_duration_ms,
            events=events_schema
        )
