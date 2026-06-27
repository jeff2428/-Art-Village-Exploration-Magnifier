"""Logging configuration re-export for Art Village Exploration Magnifier.

All logging setup is in shared/logging_setup.py — this module exists so that
flet_app/ and live_app_extract/ can import from a single source of truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

# Import with explicit module name to avoid circular import with self
import shared.logging_setup as _shared_logging  # noqa: E402

setup_logging = _shared_logging.setup_logging
