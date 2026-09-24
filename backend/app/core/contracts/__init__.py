"""
SatQuery AI — Architectural Contracts for Future Phases (Phase 2 to 10)
Defines interfaces for:
- AnalysisAgent (agentic orchestration)
- SpecialistModel (RS-VLM, Grounding, Change Detection)
- ToolRegistry (remote-sensing tool catalog)
"""
from .agent import AnalysisAgent
from .specialist import SpecialistModel
from .tools import ToolRegistry

__all__ = ["AnalysisAgent", "SpecialistModel", "ToolRegistry"]
