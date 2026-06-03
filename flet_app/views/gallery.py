from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft
from components.illustrations import PAW_PRINTS, SECTION_ICONS, SHELL_GINGER_LEAF
from plant_api import confidence_text
from ui_theme import THEME, border_all, soft_card


def build_gallery_card(
    name: str,
    item: dict[str, Any],
    on_click: Callable[[str, dict[str, Any]], None] | None = None,
    on_delete: Callable[[str], None] | None = None,
) -> ft.Container:
    icon = item.get("emoji", SHELL_GINGER_LEAF if item.get("type") == "plant" else PAW_PRINTS)
    is_low_confidence = item.get("is_low_confidence", False)
    badge = "⚠️" if is_low_confidence else ""
    subtitle = confidence_text(item) or item.get("role", "")

    card = ft.Container(
        bgcolor=THEME["CARD_BG"],
        border_radius=12, padding=12,
        alignment=ft.Alignment(0, 0),
        border=border_all(1, THEME["CARD_BORDER_ALT"]),
        shadow=ft.BoxShadow(blur_radius=10, color=THEME["SHADOW_GALLERY"], offset=ft.Offset(0, 5)),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        tooltip=f"{name} 詳細介紹",
        on_click=lambda _event, item_name=name, item_data=item: on_click(item_name, item_data) if on_click else None,
        on_long_press=lambda _event, item_name=name: on_delete(item_name) if on_delete else None,
        on_hover=lambda e: _on_card_hover(card, e),
        content=ft.Column(
            controls=[
                ft.Text(f"{icon} {badge} {name}", size=14, weight=ft.FontWeight.W_800, color=THEME["TITLE"]),
                ft.Text(subtitle, size=11, color=THEME["BODY"]),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return card


def _on_card_hover(card: ft.Container, event: ft.ControlEvent) -> None:
    """Handle gallery card hover animation."""
    card.scale = 1.04 if event.data == "true" else 1.0
    card.shadow = [
        ft.BoxShadow(
            blur_radius=18 if event.data == "true" else 10,
            color=THEME["SHADOW_GALLERY"],
            offset=ft.Offset(0, 8 if event.data == "true" else 5),
        ),
    ]
    card.update()


def build_gallery_panel(
    grid: ft.GridView,
    empty_state: ft.Container,
    on_clear: Callable | None = None,
) -> ft.Container:
    """Build the gallery panel shell with header, grid, empty state."""
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
                    spacing=8, alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Stack(controls=[grid, empty_state], width=380, height=260),
            ],
            spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
    )
