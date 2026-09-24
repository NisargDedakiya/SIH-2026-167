"""
Report Generator for SatQuery AI Benchmark & Evaluation Engine.
Coordinates JSON artifacts, markdown tables, and HTML reports.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from evaluation.reports.html import generate_html_report
from evaluation.reports.tables import format_markdown_table


class ReportGenerator:
    """
    Coordinates creation of machine-readable and human-readable evaluation reports.
    """

    @staticmethod
    def build_final_report(
        system_version: str,
        models: Dict[str, str],
        datasets_status: Dict[str, Dict[str, Any]],
        task_results: Dict[str, Dict[str, Any]],
        agent_results: Dict[str, Any],
        calibration_results: Dict[str, Any],
        performance_results: Dict[str, Any],
        error_analysis: Dict[str, Any],
        qualitative_samples: List[Dict[str, Any]],
        limitations: List[str],
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Builds artifacts/evaluation/final_evaluation_report.html and summary JSON.
        """
        out_dir = output_dir or (Path("artifacts") / "evaluation")
        out_dir.mkdir(parents=True, exist_ok=True)

        html_str = generate_html_report(
            system_version=system_version,
            models=models,
            datasets_status=datasets_status,
            task_results=task_results,
            agent_results=agent_results,
            calibration_results=calibration_results,
            performance_results=performance_results,
            error_analysis=error_analysis,
            qualitative_samples=qualitative_samples,
            limitations=limitations,
        )

        html_file = out_dir / "final_evaluation_report.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_str)

        # Also write summary JSON matrix
        matrix_file = out_dir / "evaluation_matrix.json"
        with open(matrix_file, "w", encoding="utf-8") as f:
            json.dump({
                "system_version": system_version,
                "models": models,
                "datasets": datasets_status,
                "tasks": task_results,
                "agent": agent_results,
                "calibration": calibration_results,
                "performance": performance_results,
                "error_analysis": error_analysis,
            }, f, indent=2)

        return html_file
