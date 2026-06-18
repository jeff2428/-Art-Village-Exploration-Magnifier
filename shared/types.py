"""Shared type definitions for Art Village Exploration Magnifier."""

from __future__ import annotations

from typing import Any, Callable, Protocol

import flet as ft


# --- Callbacks ---------------------------------------------------------------
VoidControlEventCallback = Callable[[ft.ControlEvent | None], None]
CreateBackgroundTask = Callable[[Any], None]
ShowGalleryCardCallback = Callable[[str, dict[str, Any]], None]


# --- Protocols ---------------------------------------------------------------
class CameraProtocol(Protocol):
    """Interface for camera manager instances."""

    async def initialize(self) -> None: ...  # noqa: D102
    async def pause_preview(self) -> None: ...  # noqa: D102
    apply_theme_colors: Callable[[], None]


# --- Data types --------------------------------------------------------------
PlantEntry = dict[str, Any]
AnimalEntry = dict[str, Any]
Pokedex = dict[str, PlantEntry | AnimalEntry]
