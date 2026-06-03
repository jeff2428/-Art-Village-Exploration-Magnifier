from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft
from pokedex_manager import load_animals_db_dynamic
from ui_theme import THEME, border_all, section_label


def animal_card(
    name: str,
    data: dict[str, Any],
    on_click: Callable[[str], None] | None = None,
) -> ft.Container:
    """Build stylized animal card. From main.py lines 1211-1248."""
    portrait_src = data.get("portrait", "")
    portrait_preview: ft.Control
    if portrait_src:
        portrait_preview = ft.Container(
            width=56, height=56, border_radius=14, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Image(src=portrait_src, fit=ft.BoxFit.COVER),
        )
    else:
        portrait_preview = ft.Container(
            width=56, height=56, border_radius=14,
            bgcolor=THEME["PERENUAL_BG"], alignment=ft.Alignment(0, 0),
            content=ft.Text(data.get("emoji", "🐾"), size=24),
        )
    return ft.Container(
        bgcolor=THEME["CARD_BG"],
        border_radius=18, padding=16,
        border=border_all(1, THEME["CARD_BORDER_ALT"]),
        shadow=ft.BoxShadow(blur_radius=14, color=THEME["SHADOW_CARD2"], offset=ft.Offset(0, 8)),
        on_click=lambda _event, pet=name: on_click(pet) if on_click else None,
        content=ft.Row(
            controls=[
                portrait_preview,
                ft.Column(
                    controls=[
                        ft.Text(name, size=19, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text(data.get("role", ""), size=13, weight=ft.FontWeight.W_700,
                               color=THEME["ANIMAL_ROLE"]),
                    ],
                    spacing=2, expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=THEME["MUTED"]),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def get_animals_view(page: ft.Page) -> ft.Column:
    """Build full animal mode view. From main.py lines 1250-1275."""
    animals = load_animals_db_dynamic()
    return ft.Column(
        controls=[
            section_label("🐾", "認識動物"),
            ft.Text("點擊卡片，打開牠的介紹卡片。", size=14, color=THEME["BODY"]),
            ft.TextButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.EDIT_NOTE, size=16),
                        ft.Text("開啟動物管理頁"),
                    ],
                    spacing=4,
                ),
                tooltip="在獨立頁面管理 admin/animals.json",
                on_click=lambda _event: page.launch_url("./admin/animals.html"),
            ),
            ft.Column(
                controls=[animal_card(name, data) for name, data in animals.items()],
                spacing=12,
            ),
        ],
        spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
