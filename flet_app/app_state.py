from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import flet as ft


@dataclass
class AppState:
    page: ft.Page
    pokedex: dict[str, dict[str, Any]] = field(default_factory=dict)
    cameras: list[Any] = field(default_factory=list)
    selected_camera_index: int = 0
    camera_ready: bool = False
    camera_initializing: bool = False
    is_dark_mode: bool = False
    recognition_loading_visible: bool = False
    zoom_level: float = 1.0
    background_tasks: set[asyncio.Task] = field(default_factory=set)
    animals_view: ft.Column | None = None

    # UI controls — assigned during build
    welcome_screen: ft.Container | None = None
    start_button: ft.ElevatedButton | None = None
    loading_emoji: ft.Text | None = None
    loading_message: ft.Text | None = None
    status: ft.Text | None = None
    busy_ring: ft.ProgressRing | None = None
    restart_camera_button: ft.TextButton | None = None
    grid: ft.GridView | None = None
    gallery_empty_state: ft.Container | None = None
    camera: Any = None
    camera_preview_slot: ft.Container | None = None
    handle_slot: ft.Container | None = None
    content_area: ft.Container | None = None
    _gallery_card_map: dict[str, ft.Container] = field(default_factory=dict)
    mode: ft.RadioGroup | None = None
    organ_mode: ft.SegmentedButton | None = None
    shell: ft.Container | None = None
