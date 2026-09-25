"""
Forwarding proxy to canonical adapter validation in backend/training/adapter_validation.py.
"""
import sys
from pathlib import Path

_backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

from training.adapter_validation import *  # noqa: F401, F403
