from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid


class AnalysisAgent(ABC):
    """
    Contract for the SatQuery Multi-Modal Agentic Orchestrator (Phase 3+).
    Responsible for:
    - Interpreting natural language user queries
    - Inspecting geospatial metadata of referenced images
    - Routing sub-tasks to specialist remote sensing models
    - Synthesizing evidence, confidence, and visual grounded outputs
    - Producing execution traces
    """

    @abstractmethod
    async def analyze(
        self,
        query: str,
        image_ids: List[uuid.UUID],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agentic analysis over single or paired remote-sensing imagery.
        
        Args:
            query: Natural language query (e.g. "Identify solar farms in this optical image")
            image_ids: One or more image identifiers (single, bi-temporal pair, or optical+SAR)
            context: Optional conversational history or geographic bounds filter
            
        Returns:
            Dictionary containing answer, visual evidence, confidence score, and execution trace.
        """
        raise NotImplementedError("AnalysisAgent will be implemented in Phase 3.")
