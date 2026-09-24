"""
Domain exceptions for the SatQuery Agentic Orchestration Layer.
"""


class AgentException(Exception):
    """Base exception for all Agent errors."""
    pass


class QueryClassificationError(AgentException):
    """Raised when query intent cannot be classified or is malformed."""
    pass


class AmbiguousQueryError(AgentException):
    """
    Raised when user query is ambiguous, triggering a controlled clarification request
    rather than guessing a random specialist tool.
    """
    def __init__(self, message: str, clarification_prompt: str):
        super().__init__(message)
        self.clarification_prompt = clarification_prompt


class CapabilityUnavailableError(AgentException):
    """
    Raised when a requested task (e.g. Change Detection, Grounding) is recognized
    but not available in the current phase.
    Prevents silent fallback to incorrect tools.
    """
    def __init__(self, task: str, message: str):
        super().__init__(message)
        self.task = task


class PlanExecutionError(AgentException):
    """Raised when an error occurs during workflow execution."""
    pass


class ParameterValidationError(AgentException):
    """Raised when tool inputs or parameters fail strict schema validation."""
    pass
