"""
JSON Exporter for SatQuery Analysis Reports.
Produces normalized, machine-readable JSON format.
"""

import json
from typing import Any, Dict
from app.reports.schemas import AnalysisReport


class JsonReportExporter:
    @classmethod
    def export(cls, report: AnalysisReport) -> str:
        """Serializes the AnalysisReport to formatted JSON."""
        return report.model_dump_json(indent=2)

    @classmethod
    def export_dict(cls, report: AnalysisReport) -> Dict[str, Any]:
        """Returns the AnalysisReport as a Python dictionary."""
        return report.model_dump()
