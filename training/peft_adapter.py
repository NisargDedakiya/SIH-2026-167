"""
Forwarding proxy to canonical LoRAManager implementation in backend/training/peft_adapter.py.
Ensures identical LoRA runtime logic across both training scripts and backend API inference.
"""
import sys
from pathlib import Path

_backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

from training.peft_adapter import *  # noqa: F401, F403
