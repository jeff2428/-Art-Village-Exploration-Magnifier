"""Build configuration for Art Village Exploration Magnifier.

Imports all values from shared/config.py — no overrides needed in flet_app/.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SHARED_DIR = next(
    (
        candidate
        for candidate in (
            Path(__file__).resolve().parent / "shared",
            Path(__file__).resolve().parents[1] / "shared",
        )
        if (candidate / "config.py").exists()
    ),
    Path(__file__).resolve().parents[1] / "shared",
)
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

# Import all shared config values (no overrides needed)
from config import (  # noqa: F401, E402
    CAMERA_GET_AVAILABLE_TIMEOUT,
    CAMERA_INITIALIZE_TIMEOUT,
    CAMERA_PREVIEW_OFFSET,
    CAMERA_PREVIEW_SIZE,
    CONTENT_MAX_WIDTH,
    CONTENT_MIN_PADDING,
    FONT_HERO,
    IMAGE_COMPRESSION_QUALITY,
    LOW_CONFIDENCE_THRESHOLD,
    MAX_CAMERA_INIT_ATTEMPTS,
    MAX_CARD_IMAGE_DATA_URL_LENGTH,
    MAX_METADATA_RETRIES,
    MIN_CAMERA_ZOOM,
    POKEDEX_SAVE_DEBOUNCE_DELAY,
    WORKER_URL,
)
