"""
Analysis Package Exporter for SatQuery.
Assembles a complete, self-contained, sanitized .zip archive (Part 26 & Part 29).
"""

import io
import json
import zipfile
from typing import Any, Dict, Optional

from app.reports.schemas import AnalysisReport
from app.reports.json_exporter import JsonReportExporter
from app.reports.html_exporter import HtmlReportExporter
from app.reports.pdf_exporter import PdfReportExporter


class AnalysisPackageExporter:
    @classmethod
    def export(
        cls,
        report: AnalysisReport,
        trace_data: Optional[Dict[str, Any]] = None,
        raw_evidence_bytes: Optional[Dict[str, bytes]] = None
    ) -> bytes:
        """
        Compiles analysis.json, report.html, report.pdf, metadata.json,
        trace.json, evidence images, and README.txt into an in-memory ZIP archive.
        """
        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. JSON analysis
            json_str = JsonReportExporter.export(report)
            zf.writestr("analysis.json", json_str)

            # 2. Interactive HTML report
            html_str = HtmlReportExporter.export(report)
            zf.writestr("report.html", html_str)

            # 3. Publication PDF report
            pdf_bytes = PdfReportExporter.export(report)
            zf.writestr("report.pdf", pdf_bytes)

            # 4. Metadata summary
            meta = {
                "report_id": report.report_id,
                "analysis_id": report.analysis_id,
                "generated_at": report.generated_at,
                "system": report.system_title,
                "problem_statement": report.problem_statement,
                "query": report.query,
                "task": report.detected_task,
                "models": [m.model_dump() for m in report.models],
                "confidence": report.confidence_percentage,
                "reproducibility_token": report.reproducibility_token,
            }
            zf.writestr("metadata.json", json.dumps(meta, indent=2))

            # 5. Observable Trace Events
            trace_payload = trace_data or {
                "analysis_id": report.analysis_id,
                "agent_run_id": report.agent_run_id,
                "milestones": [m.model_dump() for m in report.execution_milestones],
            }
            zf.writestr("trace.json", json.dumps(trace_payload, indent=2))

            # 6. Evidence artifacts (if available)
            if raw_evidence_bytes:
                for fname, b_data in raw_evidence_bytes.items():
                    # Sanitize filename to prevent directory traversal
                    clean_name = fname.replace("..", "").replace("/", "").replace("\\", "")
                    zf.writestr(f"evidence/{clean_name}", b_data)

            # 7. README.txt
            readme = f"""======================================================================
SATQUERY AI — ANALYSIS PACKAGE
======================================================================
Report ID:     {report.report_id}
Analysis ID:   {report.analysis_id}
Generated:     {report.generated_at}
Task:          {report.detected_task}
Query:         {report.query}
Confidence:    {report.confidence_percentage or 'Uncalibrated'}
Token:         {report.reproducibility_token}

CONTENTS:
- analysis.json: Machine-readable complete analysis report
- report.html:   Interactive, browser-viewable presentation
- report.pdf:    Formal publication-grade printable PDF document
- metadata.json: High-level geospatial and execution parameters
- trace.json:    Observable execution trace events and timing
- evidence/:     Associated spatial bounding box / change overlays
- README.txt:    This package manifest

ISRO Smart India Hackathon · Problem Statement 26167
Department of Space, Government of India
======================================================================
"""
            zf.writestr("README.txt", readme)

        return buf.getvalue()
