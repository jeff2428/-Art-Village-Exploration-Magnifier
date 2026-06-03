from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft
from ui_theme import THEME, border_all


def plant_card(
    name: str,
    data: dict[str, Any],
    on_click: Callable[[str, dict[str, Any]], None] | None = None,
) -> ft.Container:
    """Build a stylized plant result card. From main.py lines 1178-1209."""
    confidence = data.get("confidence", 0)
    is_low_confidence = data.get("is_low_confidence", False)
    badge = "⚠️" if (is_low_confidence and confidence > 0) else ""
    return ft.Container(
        bgcolor=THEME["CARD_BG"],
        border_radius=18, padding=16,
        border=border_all(1, THEME["CARD_BORDER_ALT"]),
        shadow=ft.BoxShadow(blur_radius=14, color=THEME["SHADOW_CARD2"], offset=ft.Offset(0, 8)),
        on_click=lambda _event, plant_name=name: on_click(plant_name, data) if on_click else None,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(f"{data['emoji']} {badge}", size=34),
                        ft.Column(
                            controls=[
                                ft.Text(name, size=19, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                                ft.Text(f"置信度: {confidence}%" if confidence > 0 else "",
                                       size=13, weight=ft.FontWeight.W_700, color=THEME["BODY"]),
                            ],
                            spacing=2, expand=True,
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=THEME["MUTED"]),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def organ_selector(organ_mode: ft.SegmentedButton) -> ft.Container:
    """Build organ selector UI. From main.py lines 1162-1176."""
    return ft.Container(
        padding=8, border_radius=12,
        bgcolor=THEME["ORGAN_BG"],
        border=border_all(1, THEME["DETAIL_BORDER"]),
        content=ft.Row(
            controls=[
                ft.Text("拍攝部位", size=12, weight=ft.FontWeight.W_900, color=THEME["BODY"]),
                organ_mode,
            ],
            spacing=8, alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        ),
    )


def _build_plant_view(
    magnifier_body: ft.Stack,
    busy_ring: ft.ProgressRing,
    status: ft.Text,
    restart_camera_button: ft.TextButton,
    organ_mode: ft.SegmentedButton,
) -> ft.Column:
    """Build full plant mode view. From main.py lines 1277-1291."""
    return ft.Column(
        controls=[
            magnifier_body, organ_selector(organ_mode),
            ft.Row(
                controls=[busy_ring, status],
                spacing=8, alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            restart_camera_button,
        ],
        spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
