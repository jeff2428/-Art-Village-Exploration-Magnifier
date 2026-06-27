"""Shell UI builder — extracts all layout / mode-switching UI from main.py."""

from __future__ import annotations

from typing import Any

import flet as ft
from app_state import AppState
from app_types import AppMode
from build_config import CONTENT_MAX_WIDTH, CONTENT_MIN_PADDING
from components.illustrations import MODE_ICONS
from ui_theme import FONT_HERO, THEME


def build_mode_selector(
    selected_mode: dict[str, str],
    switch_callback: Any,
) -> ft.Row:
    """Build the plant / animal mode toggle row."""

    def option(value: str, icon: str, label: str) -> ft.TextButton:
        is_active = selected_mode["value"] == value

        return ft.TextButton(
            content=ft.Column(
                controls=[
                    ft.Text(icon, size=20 if is_active else 16),
                    ft.Text(
                        label,
                        size=13 if is_active else 12,
                        weight=(
                            ft.FontWeight.W_900 if is_active else ft.FontWeight.W_700
                        ),
                        color=THEME["ACCENT"] if is_active else THEME["BODY"],
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=lambda _event, next_value=value: switch_callback(next_value),
        )

    return ft.Row(
        controls=[
            option("plant", MODE_ICONS[AppMode.PLANT], "植物"),
            option("animal", MODE_ICONS[AppMode.ANIMAL], "動物"),
        ],
        spacing=24,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def build_shell(
    page: ft.Page,
    state: AppState,
    mode: ft.Container,
    content_area: ft.Container,
    gallery_service: Any,  # GalleryService instance
    camera: Any,  # CameraManager instance
    busy_ring: ft.ProgressRing,
    status: ft.Text,
    restart_camera_button: ft.TextButton,
    organ_mode: ft.SegmentedButton,
) -> ft.Container:
    """Build the full app shell (header + mode selector + content + gallery)."""

    def _rebuild_visible_shell() -> None:
        # Remove old controls from parents
        for ctrl in [gallery_service.grid, gallery_service.gallery_empty_state, mode, content_area]:
            if ctrl is not None and ctrl.parent is not None:
                try:
                    parent = ctrl.parent
                    if hasattr(parent, "controls") and ctrl in parent.controls:
                        parent.controls.remove(ctrl)
                    elif hasattr(parent, "content") and parent.content == ctrl:
                        parent.content = None
                except (AttributeError, ValueError):
                    pass

        toggle_icon = ft.Icons.DARK_MODE if not state.is_dark_mode else ft.Icons.LIGHT_MODE
        toggle_tip = "深色模式" if not state.is_dark_mode else "淺色模式"

        mode.content = build_mode_selector(
            {"value": state.current_mode.value},  # type: ignore[attr-defined]
            lambda next_value: None,  # placeholder — real callback set externally
        )

        gallery_panel = _build_gallery_panel(
            gallery_service.grid,
            gallery_service.gallery_empty_state,
            on_clear=gallery_service.confirm_clear,
        )

        if state.current_mode == AppMode.ANIMAL:  # type: ignore[attr-defined]
            from views import animal_view as av

            new_content = av.get_animals_view(
                page,
                lambda name: gallery_service.show_gallery_card(name, {}),  # placeholder
            )
        else:
            from views.plant_view import _build_plant_view

            new_content = _build_plant_view(
                camera.magnifier_body, busy_ring, status, restart_camera_button, organ_mode
            )

        content_area.content = new_content

        shell_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("探險放大鏡", size=FONT_HERO, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text("\U0001f50d", size=FONT_HERO - 2),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=toggle_icon,
                            icon_color=THEME["ACCENT"],
                            tooltip=toggle_tip,
                            on_click=None,  # placeholder — set externally
                        ),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                _soft_card(mode, padding=10),
                content_area,
                gallery_panel,
            ],
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return shell_content  # type: ignore[return-value]

    shell = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        visible=False,
    )

    return shell


def _build_gallery_panel(
    grid: ft.GridView,
    empty_state: ft.Container,
    on_clear: Any = None,
) -> ft.Container:
    """Build the gallery panel shell."""
    from components.illustrations import SECTION_ICONS
    from ui_theme import soft_card

    return soft_card(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(SECTION_ICONS["gallery_header"], size=30),
                        ft.Text("探險圖鑑", size=28, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            icon_color=THEME["ACCENT"],
                            tooltip="清除收藏內容",
                            on_click=on_clear,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Stack(controls=[grid, empty_state], width=380, height=260),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
    )


def _soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
    """Thin wrapper around ui_theme.soft_card for shell building."""
    from ui_theme import soft_card

    return soft_card(content, padding=padding)
