"""Shared configuration for Art Village Exploration Magnifier.

This module centralizes all constants and supports environment variable overrides.
Both flet_app/ and live_app_extract/ import from here to eliminate duplication.
"""

from __future__ import annotations

import os


# --- Image processing --------------------------------------------------------
MAX_IMAGE_WIDTH: int = int(os.getenv("AV_MAX_IMAGE_WIDTH", "800"))
IMAGE_COMPRESSION_QUALITY: int = int(os.getenv("AV_IMAGE_COMPRESSION_QUALITY", "85"))
LOW_CONFIDENCE_THRESHOLD: float = float(os.getenv("AV_LOW_CONFIDENCE_THRESHOLD", "50.0"))

# --- Camera ------------------------------------------------------------------
CAMERA_PREVIEW_SIZE: int = int(os.getenv("AV_CAMERA_PREVIEW_SIZE", "420"))
CAMERA_PREVIEW_OFFSET: int = int(os.getenv("AV_CAMERA_PREVIEW_OFFSET", "-58"))
MIN_CAMERA_ZOOM: float = float(os.getenv("AV_MIN_CAMERA_ZOOM", "1.0"))
MAX_CAMERA_ZOOM: float = float(os.getenv("AV_MAX_CAMERA_ZOOM", "3.0"))
CAMERA_ZOOM_STEP: float = float(os.getenv("AV_CAMERA_ZOOM_STEP", "0.25"))
LENS_VIEWPORT_SIZE: int = int(os.getenv("AV_LENS_VIEWPORT_SIZE", "304"))
LENS_FRAME_SIZE: int = int(os.getenv("AV_LENS_FRAME_SIZE", "336"))
LENS_FRAME_PADDING: int = int(os.getenv("AV_LENS_FRAME_PADDING", "11"))

# --- Camera initialization ---------------------------------------------------
MAX_CAMERA_INIT_ATTEMPTS: int = int(os.getenv("AV_MAX_CAMERA_INIT_ATTEMPTS", "3"))
CAMERA_INITIALIZE_TIMEOUT: float = float(os.getenv("AV_CAMERA_INITIALIZE_TIMEOUT", "5.0"))
CAMERA_GET_AVAILABLE_TIMEOUT: float = float(os.getenv("AV_CAMERA_GET_AVAILABLE_TIMEOUT", "3.0"))

# --- Pokedex -----------------------------------------------------------------
POKEDEX_SAVE_DEBOUNCE_DELAY: float = float(os.getenv("AV_POKEDEX_SAVE_DEBOUNCE_DELAY", "0.5"))
MAX_POKEDEX_STORAGE_BYTES: int = int(os.getenv("AV_MAX_POKEDEX_STORAGE_BYTES", "50000"))

# --- Worker/API --------------------------------------------------------------
WORKER_URL: str = os.getenv(
    "AV_WORKER_URL",
    "https://art-village-magnifier.jeff2428.workers.dev",
)
MAX_METADATA_RETRIES: int = int(os.getenv("AV_MAX_METADATA_RETRIES", "3"))
METADATA_REQUEST_TIMEOUT: float = float(os.getenv("AV_METADATA_REQUEST_TIMEOUT", "15.0"))
WORKER_REQUEST_TIMEOUT: float = float(os.getenv("AV_WORKER_REQUEST_TIMEOUT", "30.0"))

# --- UI/Layout ---------------------------------------------------------------
CONTENT_MAX_WIDTH: int = int(os.getenv("AV_CONTENT_MAX_WIDTH", "430"))
CONTENT_MIN_PADDING: int = int(os.getenv("AV_CONTENT_MIN_PADDING", "16"))
FONT_HERO: int = int(os.getenv("AV_FONT_HERO_SIZE", "28"))

# --- Storage -----------------------------------------------------------------
MAX_CARD_IMAGE_DATA_URL_LENGTH: int = int(os.getenv("AV_MAX_CARD_IMAGE_DATA_URL_LENGTH", "180000"))
