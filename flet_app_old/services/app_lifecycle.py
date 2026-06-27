"""App lifecycle — manages LANDING → PLANT/ANIMAL state transitions."""

from __future__ import annotations

import asyncio
from typing import Any

import flet as ft
from app_state import AppState
from app_types import AppMode
from camera_utils import MIN_CAMERA_ZOOM
from pokedex_manager import (
    flush_pokedex_save,
    save_dark_mode_preference,
    sync_animals_from_worker,
)


class AppLifecycle:
    """Orchestrates app state transitions and background tasks."""

    def __init__(
        self,
        page: ft.Page,
        state: AppState,
        gallery_service: Any,  # GalleryService
        camera: Any,  # CameraManager
        status_text: ft.Text,
        create_background_task: Any,
        show_gallery_card_callback: Any = None,
    ) -> None:
        self._page = page
        self._state = state
        self._gallery_service = gallery_service
        self._camera = camera
        self._status_text = status_text
        self._create_background_task = create_background_task
        self._show_gallery_card = show_gallery_card_callback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_exploration(
        self,
        shell: ft.Container,
        welcome_screen: ft.Container,
        start_button: ft.ElevatedButton,
        camera_manager: Any,  # CameraManager for initialize()
    ) -> None:
        """Transition from landing to plant mode."""
        try:
            setattr(start_button, "text", "準備中...")
            start_button.disabled = True
            await asyncio.sleep(0)

            self._state.current_mode = AppMode.PLANT
            self._state.zoom_level = MIN_CAMERA_ZOOM

            # Build shell content (plant view)
            from views.plant_view import _build_plant_view

            from services.shared_controls import organ_mode_button

            shell.content = _build_plant_view(
                camera_manager.magnifier_body,
                ft.ProgressRing(width=22, height=22, stroke_width=3),  # placeholder
                self._status_text,
                ft.TextButton(),  # placeholder
                organ_mode_button(),
            )

            if self._state.pokedex:
                self._gallery_service.refresh(update_page=False)

            shell.visible = True
            welcome_screen.visible = False
            self._page.update()
            await self._page.scroll_to(offset=0)
            self._page.update()

            self._create_background_task(camera_manager.initialize())
        except Exception as error:
            self._show_error_page("探險流程啟動失敗", str(error))

    async def switch_mode(self, value: str) -> None:
        """Switch between plant and animal modes."""
        if value == self._state.current_mode.value:  # type: ignore[attr-defined]
            return

        self._state.current_mode = AppMode.PLANT if value == "plant" else AppMode.ANIMAL  # type: ignore[assignment]

        if value == "animal":
            await self._hide_camera_preview()
            self._create_background_task(sync_animals_from_worker())
        else:
            await self._restore_camera_preview()

    def toggle_dark_mode(self) -> None:
        """Toggle dark/light theme."""
        self._state.is_dark_mode = not self._state.is_dark_mode

        from ui_theme import THEME, apply_theme

        apply_theme(self._state.is_dark_mode)
        self._page.theme_mode = (
            ft.ThemeMode.DARK if self._state.is_dark_mode else ft.ThemeMode.LIGHT
        )
        self._page.bgcolor = THEME["PAGE_BG"]

        # Notify camera manager to update colors
        if hasattr(self._camera, "apply_theme_colors"):
            self._camera.apply_theme_colors()

        self._create_background_task(
            save_dark_mode_preference(self._state.is_dark_mode)
        )

    async def on_page_close(self) -> None:
        """Flush pokedex before app closes."""
        await flush_pokedex_save()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _hide_camera_preview(self) -> None:
        self._state.camera_ready = False
        current_camera = self._state.camera
        self._state.camera = None
        if hasattr(self._camera, "camera_preview_slot"):
            self._camera.camera_preview_slot.visible = False
            self._camera.camera_preview_slot.content = (
                self._camera.camera_placeholder
            )
        if current_camera is not None:
            try:
                await current_camera.pause_preview()
            except (AttributeError, RuntimeError):
                pass

    async def _restore_camera_preview(self) -> None:
        if hasattr(self._camera, "camera_preview_slot"):
            self._state.camera_ready = False
            self._camera.camera_preview_slot.visible = True
            self._camera.camera_preview_slot.content = (
                self._camera.camera_placeholder
            )
        await self._camera.initialize()

    def _show_error_page(self, title: str, error: str) -> None:
        from ui_theme import THEME

        self._page.clean()
        self._page.add(
            ft.Container(
                padding=24,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    [
                        ft.Text(title, size=26, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text(error, size=14, color=THEME["BODY_DARK"], selectable=True),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        self._page.update()
