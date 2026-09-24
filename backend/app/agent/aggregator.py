"""
Result Aggregator for SatQuery AI.
Combines and normalizes specialist tool outputs into the standard final agent response contract.
"""

import uuid
from typing import Any, Dict, List, Optional

from app.agent.schemas import ConfidenceSchema, ToolSummarySchema


class ResultAggregator:
    """
    Normalizes and aggregates outputs from one or more specialist analytical tools.
    Harmonizes answers, calibrated confidences, and evidence sets.
    """

    @classmethod
    def aggregate(
        cls,
        task: str,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregates outputs into normalized final response attributes.
        """
        if not tool_results:
            return {
                "analysis_id": None,
                "answer": "No analytical result generated.",
                "confidence": ConfidenceSchema(score=0.0, method="none"),
                "tools": [],
                "evidence": [],
            }

        # Single-tool workflow (Phase 3 & Phase 5 primary)
        primary = tool_results[0]
        analysis_id = primary.get("analysis_id")
        if isinstance(analysis_id, str):
            analysis_id = uuid.UUID(analysis_id)

        answer = (
            primary.get("answer")
            or primary.get("caption")
            or (primary.get("result", {}).get("answer") if isinstance(primary.get("result"), dict) else None)
            or ""
        )

        conf_data = primary.get("confidence", {})
        if isinstance(conf_data, dict):
            score = float(conf_data.get("score", 0.85))
            method = str(conf_data.get("method", "calibrated_score"))
        elif isinstance(conf_data, (float, int)):
            score = float(conf_data)
            method = "score"
        else:
            score = 0.85
            method = "heuristic"

        # Bounded score
        score = max(0.0, min(1.0, score))

        tools_used: List[ToolSummarySchema] = []
        for res in tool_results:
            tools_used.append(
                ToolSummarySchema(
                    name=res.get("tool_name", "unknown_tool"),
                    version=res.get("tool_version", "1.0.0"),
                    task=res.get("task", task),
                    status="completed",
                    description=res.get("description")
                )
            )

        evidence = primary.get("evidence", [])
        artifact_key = primary.get("artifact_key")
        if not artifact_key and evidence:
            for ev in evidence:
                if isinstance(ev, dict) and ev.get("artifact_key"):
                    artifact_key = ev["artifact_key"]
                    break

        pair_id = primary.get("pair_id")
        if not pair_id and isinstance(primary.get("result"), dict):
            pair_id = primary.get("result", {}).get("pair_id")
        if isinstance(pair_id, str):
            try:
                pair_id = uuid.UUID(pair_id)
            except Exception:
                pass

        regions = primary.get("regions")
        if not regions and isinstance(primary.get("result"), dict):
            regions = primary.get("result", {}).get("regions", [])

        change_metrics = primary.get("change")
        if not change_metrics and isinstance(primary.get("result"), dict):
            change_metrics = {
                k: v for k, v in primary["result"].items()
                if k in ["changed", "change_score", "change_percentage", "regions_count"]
            }

        fb = primary.get("fallback")
        is_adapted = primary.get("is_adapted", False)
        adapter_id = "satquery-rs-v1" if is_adapted else None

        # Tripartite observation taxonomy
        observations = primary.get("observations")
        if not observations or not isinstance(observations, dict):
            observed_items = []
            if answer:
                observed_items.append(f"Model identified feature response: {answer}")
            if regions:
                observed_items.append(f"Localized {len(regions)} spatial target region(s) in imagery.")
            if change_metrics and change_metrics.get("change_percentage"):
                observed_items.append(f"Detected {change_metrics.get('change_percentage')}% surface variation between temporal acquisitions.")

            observations = {
                "observed": observed_items or ["Visual spectrum inspection completed."],
                "inferred": ["Feature characteristics align with typical remote-sensing patterns."],
                "uncertain": ["Spatial resolution limits and atmospheric/speckle conditions apply."]
            }

        return {
            "analysis_id": analysis_id,
            "pair_id": pair_id,
            "answer": answer,
            "confidence": ConfidenceSchema(score=score, method=method),
            "tools": tools_used,
            "evidence": evidence,
            "regions": regions or [],
            "change_metrics": change_metrics,
            "artifact_key": artifact_key,
            "is_adapted": is_adapted,
            "adapter_id": adapter_id,
            "fallback_used": bool(fb),
            "fallback_reason": fb.get("reason") if isinstance(fb, dict) else None,
            "observations": observations,
        }
