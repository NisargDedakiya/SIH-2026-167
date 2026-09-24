"""
FastAPI router for SatQuery AI Benchmark & Evaluation Engine (Phase 8).
Provides read-only queries into benchmark datasets, task scorecards,
calibration metrics, latency distributions, and evaluation runs.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# Resolve workspace root and artifacts evaluation directory
EVAL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "evaluation"
MATRIX_FILE = EVAL_DIR / "evaluation_matrix.json"


def _load_matrix() -> Dict[str, Any]:
    if not MATRIX_FILE.exists():
        # Fallback empty matrix if not yet run
        return {
            "system_version": "1.0.0 (Phase 8)",
            "models": {},
            "datasets": {},
            "tasks": {},
            "agent": {},
            "calibration": {},
            "performance": {},
            "error_analysis": {},
        }
    try:
        with open(MATRIX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation matrix: {str(e)}")


@router.get("/matrix", response_model=Dict[str, Any])
def get_evaluation_matrix() -> Dict[str, Any]:
    """Returns the comprehensive evaluation matrix summarizing all benchmark metrics."""
    return _load_matrix()


@router.get("/datasets", response_model=Dict[str, Any])
def get_benchmark_datasets() -> Dict[str, Any]:
    """Returns all registered benchmark datasets with status, modality, and sample counts."""
    matrix = _load_matrix()
    return matrix.get("datasets", {})


@router.get("/tasks", response_model=Dict[str, Any])
def get_evaluation_tasks() -> Dict[str, Any]:
    """Returns task scorecards across VQA, Captioning, Grounding, Change, and Cross-Modal."""
    matrix = _load_matrix()
    return matrix.get("tasks", {})


@router.get("/runs", response_model=List[Dict[str, Any]])
def list_evaluation_runs(limit: int = Query(default=20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Lists saved evaluation run manifests stored in artifacts/evaluation/."""
    if not EVAL_DIR.exists():
        return []

    runs = []
    for d in sorted(EVAL_DIR.iterdir(), reverse=True):
        if d.is_dir() and d.name.startswith("eval_"):
            manifest_file = d / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        runs.append(data)
                except Exception:
                    continue
        if len(runs) >= limit:
            break
    return runs


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
def get_evaluation_run(run_id: str) -> Dict[str, Any]:
    """Returns the full manifest and summary for a specific evaluation run."""
    run_path = EVAL_DIR / run_id
    if not run_path.exists() or not run_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found.")

    manifest_file = run_path / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail=f"Manifest for run '{run_id}' not found.")

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        # Check if predictions.jsonl exists
        pred_file = run_path / "predictions.jsonl"
        predictions = []
        if pred_file.exists():
            with open(pred_file, "r", encoding="utf-8") as pf:
                for line in pf:
                    line = line.strip()
                    if line:
                        predictions.append(json.loads(line))

        manifest_data["predictions"] = predictions
        return manifest_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read run data: {str(e)}")


@router.get("/calibration", response_model=Dict[str, Any])
def get_calibration_metrics() -> Dict[str, Any]:
    """Returns Expected Calibration Error (ECE), Brier score, and binning data."""
    matrix = _load_matrix()
    return matrix.get("calibration", {})


@router.get("/errors", response_model=Dict[str, Any])
def get_error_analysis() -> Dict[str, Any]:
    """Returns error rate, failure modes, and taxonomy breakdown."""
    matrix = _load_matrix()
    return matrix.get("error_analysis", {})
