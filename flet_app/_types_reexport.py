"""Type definitions re-export for Art Village Exploration Magnifier.

All type definitions are in shared/types.py — this module exists so that
flet_app/ and live_app_extract/ can import from a single source of truth.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_TYPES_PATH = next(
    (
        candidate
        for candidate in (
            Path(__file__).resolve().parent / "shared" / "types.py",
            Path(__file__).resolve().parents[1] / "shared" / "types.py",
        )
        if candidate.exists()
    ),
    Path(__file__).resolve().parents[1] / "shared" / "types.py",
)

# Re-export types from shared/types.py
_spec = importlib.util.spec_from_file_location("shared_types", _TYPES_PATH)
_shared_types = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared_types)  # type: ignore[union-attr]

AnimalEntry = _shared_types.AnimalEntry
CameraProtocol = _shared_types.CameraProtocol
CreateBackgroundTask = _shared_types.CreateBackgroundTask
PlantEntry = _shared_types.PlantEntry
Pokedex = _shared_types.Pokedex
ShowGalleryCardCallback = _shared_types.ShowGalleryCardCallback
VoidControlEventCallback = _shared_types.VoidControlEventCallback
