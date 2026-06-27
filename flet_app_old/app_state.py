from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import flet as ft
from app_types import AppMode


@dataclass
class AppState:
    page: ft.Page
    current_mode: AppMode = AppMode.LANDING
    pokedex: dict[str, dict[str, Any]] = field(default_factory=dict)
    cameras: list[Any] = field(default_factory=list)
    selected_camera_index: int = 0
    camera_ready: bool = False
    camera_initializing: bool = False
    is_dark_mode: bool = False
    recognition_loading_visible: bool = False
    zoom_level: float = 1.0
    background_tasks: set[asyncio.Task] = field(default_factory=set)
    camera: Any = None
