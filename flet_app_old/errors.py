"""Error classes re-export for Art Village Exploration Magnifier.

All error definitions are in shared/errors.py — this module exists so that
flet_app/ and live_app_extract/ can import from a single source of truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[1]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Import with explicit module name to avoid circular import with self
import shared.errors as _shared_errors  # noqa: E402

AppError = _shared_errors.AppError
CameraError = _shared_errors.CameraError
RecognitionError = _shared_errors.RecognitionError
StorageError = _shared_errors.StorageError
worker_error_message = _shared_errors.worker_error_message
