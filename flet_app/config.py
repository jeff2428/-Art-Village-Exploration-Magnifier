"""Configuration re-export for Art Village Exploration Magnifier.

All constants are defined in shared/config.py — this module exists so that
flet_app/ and live_app_extract/ can import from a single source of truth.
"""

from __future__ import annotations

from pathlib import Path

_CONFIG_PATH = next(
    (
        candidate
        for candidate in (
            Path(__file__).resolve().parent / "shared" / "config.py",
            Path(__file__).resolve().parents[1] / "shared" / "config.py",
        )
        if candidate.exists()
    ),
    Path(__file__).resolve().parents[1] / "shared" / "config.py",
)

# Import shared config by its full module name to avoid circular imports
import importlib.util

_spec = importlib.util.spec_from_file_location("shared_config", _CONFIG_PATH)
_shared_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared_config)  # type: ignore[union-attr]

# Re-export all constants
CAMERA_GET_AVAILABLE_TIMEOUT = _shared_config.CAMERA_GET_AVAILABLE_TIMEOUT
CAMERA_INITIALIZE_TIMEOUT = _shared_config.CAMERA_INITIALIZE_TIMEOUT
CAMERA_PREVIEW_OFFSET = _shared_config.CAMERA_PREVIEW_OFFSET
CAMERA_PREVIEW_SIZE = _shared_config.CAMERA_PREVIEW_SIZE
CAMERA_ZOOM_STEP = _shared_config.CAMERA_ZOOM_STEP
CONTENT_MAX_WIDTH = _shared_config.CONTENT_MAX_WIDTH
CONTENT_MIN_PADDING = _shared_config.CONTENT_MIN_PADDING
FONT_HERO = _shared_config.FONT_HERO
IMAGE_COMPRESSION_QUALITY = _shared_config.IMAGE_COMPRESSION_QUALITY
LENS_FRAME_PADDING = _shared_config.LENS_FRAME_PADDING
LENS_FRAME_SIZE = _shared_config.LENS_FRAME_SIZE
LENS_VIEWPORT_SIZE = _shared_config.LENS_VIEWPORT_SIZE
LOW_CONFIDENCE_THRESHOLD = _shared_config.LOW_CONFIDENCE_THRESHOLD
MAX_CAMERA_INIT_ATTEMPTS = _shared_config.MAX_CAMERA_INIT_ATTEMPTS
MAX_CARD_IMAGE_DATA_URL_LENGTH = _shared_config.MAX_CARD_IMAGE_DATA_URL_LENGTH
MAX_CAMERA_ZOOM = _shared_config.MAX_CAMERA_ZOOM
MAX_IMAGE_WIDTH = _shared_config.MAX_IMAGE_WIDTH  # noqa: F405
MAX_METADATA_RETRIES = _shared_config.MAX_METADATA_RETRIES
METADATA_REQUEST_TIMEOUT = _shared_config.METADATA_REQUEST_TIMEOUT  # noqa: F405
WORKER_REQUEST_TIMEOUT = _shared_config.WORKER_REQUEST_TIMEOUT  # noqa: F405
MAX_POKEDEX_STORAGE_BYTES = _shared_config.MAX_POKEDEX_STORAGE_BYTES
MIN_CAMERA_ZOOM = _shared_config.MIN_CAMERA_ZOOM
POKEDEX_SAVE_DEBOUNCE_DELAY = _shared_config.POKEDEX_SAVE_DEBOUNCE_DELAY

# WORKER_URL is special — it may be overridden by build_config in live_app_extract/
try:
    from build_config import WORKER_URL  # noqa: F401
except ImportError:
    WORKER_URL = _shared_config.WORKER_URL  # type: ignore[name-defined]
