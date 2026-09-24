"""
Model Prediction schema for SatQuery AI Benchmark & Evaluation Engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelPrediction:
    """
    Standardized model output container across all evaluation tasks.
    """
    sample_id: str
    task: str
    model: str
    answer: Optional[str] = None
    caption: Optional[str] = None
    regions: List[Dict[str, Any]] = field(default_factory=list)
    change_mask: Optional[Any] = None
    confidence: Optional[float] = None
    confidence_method: Optional[str] = None
    latency_ms: float = 0.0
    latency_breakdown_ms: Dict[str, float] = field(default_factory=dict)
    raw_output: Dict[str, Any] = field(default_factory=dict)
    is_adapted: bool = False
    adapter_id: Optional[str] = None
    error: Optional[str] = None
