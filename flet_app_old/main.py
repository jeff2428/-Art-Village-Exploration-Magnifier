"""Art Village Exploration Magnifier — entry point (~150 lines).

Delegates UI construction to views/shell_view.py and app lifecycle to
services/app_lifecycle.py so this file stays lean.
"""

from __future__ import annotations

import asyncio
import os
import traceback
from typing import Any

import flet as ft

try:
    import flet_camera as fc  # noqa: F401
except ImportError:
    pass  # Camera not available in this environment

from app_state import AppState
from build_config import CONTENT_MAX_WIDTH, CONTENT_MIN_PADDING
from camera_utils import MIN_CAMERA_ZOOM
from logging_setup import setup_logging  # noqa: F401 — side-effect: configures logging
from pokedex_manager import (
    _preload_animals_from_idb,
    clear_legacy_snapshot_cache,
    load_cached_pokedex,
    load_dark_mode_preference,
)
from services.app_lifecycle import AppLifecycle
from services.camera_manager import CameraManager
from services.recognition import RecognitionService
from services.shared_controls import create_background_task_factory, create_shared_controls, organ_mode_button
from services.storage import GalleryService
from ui_theme import THEME, apply_theme
from views import dialogs as dv
from views import welcome as wv

APP_TITLE = "藝素村探險放大鏡"
EXPLORER_LOAD_FAILED = "探險放大鏡載入失敗"


def mark_explorer_ready(page: ft.Page | None = None) -> None:
    if page is not None:
        try:
            run_js = getattr(page, "run_js", None)
            if callable(run_js):
                run_js("window.__artVillageReady = true;")
                return
        except (AttributeError, TypeError):
            pass
    try:
        from js import window  # type: ignore
        window.__artVillageReady = True
    except (ImportError, AttributeError):
        pass


async def main(page: ft.Page) -> None:
    try:
        await _run_app(page)
    except Exception as error:
        page.clean()
        page.add(
            ft.Container(
                padding=24, alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Text(EXPLORER_LOAD_FAILED, size=26, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                    ft.Text("".join(traceback.format_exception(error)), size=14, color=THEME["BODY_DARK"], selectable=True),
                ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
        )
        page.update()
        mark_explorer_ready(page)


async def _run_app(page: ft.Page) -> None:
    # --- Page setup ----------------------------------------------------------
    page.title = APP_TITLE
    page.fonts = {
        "Noto Sans TC": "assets/fonts/NotoSansTC-Regular.ttf",
        "Noto Sans TC Bold": "assets/fonts/NotoSansTC-Bold.ttf",
        "Noto Sans TC Black": "assets/fonts/NotoSansTC-Black.ttf",
    }
    page.theme = ft.Theme(font_family="Noto Sans TC")

    # --- State ---------------------------------------------------------------
    state = AppState(page=page)
    state.pokedex = await load_cached_pokedex()
    state.is_dark_mode = await load_dark_mode_preference()
    apply_theme(state.is_dark_mode)
    await clear_legacy_snapshot_cache()
    # Preload animals from IndexedDB in background (ANIMALS_DB updated when ready)
    asyncio.create_task(_preload_animals_from_idb())
    state.zoom_level = MIN_CAMERA_ZOOM

    page.theme_mode = ft.ThemeMode.DARK if state.is_dark_mode else ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor = THEME["PAGE_BG"]
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- Shared controls -----------------------------------------------------
    status, busy_ring = create_shared_controls(state)
    organ_mode = organ_mode_button()

    selected_mode: dict[str, str] = {"value": "plant"}

    def selected_organ_value() -> str:
        if organ_mode.selected:
            return list(organ_mode.selected)[0]
        return "auto"

    create_bg_task = create_background_task_factory(page, state)

    # --- Services ------------------------------------------------------------
    async def _sync_animals() -> None:
        from pokedex_manager import sync_animals_from_worker
        await sync_animals_from_worker()
        if selected_mode["value"] == "animal":
            page.update()

    create_bg_task(_sync_animals())

    def show_gallery_card(name: str, data: dict[str, Any]) -> None:
        if data.get("type") == "animal":
            dv.show_animal_card(page, state, status, gallery_service.add_animal, name)
        else:
            dv.show_plant_card(page, state, status, name, data)

    async def on_capture_result(plant: dict[str, Any]) -> None:
        gallery_service.add_plant(plant)
        dv.show_plant_card(page, state, status, plant["zh_name"], plant)
        if plant.get("metadata_status") == "pending":
            create_bg_task(recognition_service.refresh_plant_metadata(plant))

    gallery_service = GalleryService(
        page=page, state=state, status_text=status,
        create_background_task=create_bg_task,
        show_gallery_card=show_gallery_card,
        close_dialog=lambda e: dv.close_dialog(page, e),
    )

    recognition_service = RecognitionService(
        page=page, state=state, status_text=status,
        create_background_task=create_bg_task,
        refresh_gallery=gallery_service.refresh,
    )

    camera = CameraManager(
        page=page, state=state, status_text=status, busy_ring=busy_ring,
        on_capture_result=on_capture_result,
        create_background_task=create_bg_task,
        get_selected_organ=selected_organ_value,
        is_plant_mode=lambda: selected_mode["value"] == "plant",
    )

    shell = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        visible=False,
    )

    # --- Lifecycle -----------------------------------------------------------
    lifecycle = AppLifecycle(
        page=page, state=state, gallery_service=gallery_service,
        camera=camera, status_text=status, create_background_task=create_bg_task,
        show_gallery_card_callback=show_gallery_card,
    )

    # --- UI components -------------------------------------------------------
    welcome_screen = wv.build_welcome_screen(page)
    start_button = wv.build_start_button()

    def _start_exploration(_event: Any) -> None:
        create_bg_task(lifecycle.start_exploration(shell, welcome_screen, start_button, camera))

    start_button.on_click = _start_exploration

    welcome_paper = welcome_screen.content
    assert isinstance(welcome_paper, ft.Container)
    welcome_content = welcome_paper.content
    assert isinstance(welcome_content, ft.Column)
    welcome_content.controls.append(start_button)

    page.add(welcome_screen, shell)
    page.update()
    await asyncio.sleep(0)
    mark_explorer_ready(page)

    def _on_page_resize(_event: ft.ControlEvent | None = None) -> None:
        w = min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2)
        welcome_screen.width = w
        shell.width = w
        page.update()

    page.on_resize = _on_page_resize


if os.environ.get("FLET_SKIP_RUN") != "1":
    ft.run(main)
