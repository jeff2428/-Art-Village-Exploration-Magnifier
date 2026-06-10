from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft
from components.illustrations import SECTION_ICONS
from pokedex_manager import load_animals_db_dynamic
from ui_theme import THEME, interactive_card, section_label


def animal_card(
    name: str,
    data: dict[str, Any],
    on_click: Callable[[str], None] | None = None,
) -> ft.Container:
    """Build a customer-facing animal introduction card."""
    portrait_src = data.get("portrait", "")
    description = str(data.get("desc", "")).strip()
    summary = description if len(description) <= 54 else f"{description[:52]}..."
    portrait_preview: ft.Control
    if portrait_src:
        portrait_preview = ft.Container(
            width=78, height=78, border_radius=16, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Image(src=portrait_src, fit=ft.BoxFit.COVER),
        )
    else:
        portrait_preview = ft.Container(
            width=78, height=78, border_radius=16,
            bgcolor=THEME["PERENUAL_BG"], alignment=ft.Alignment(0, 0),
            content=ft.Text(data.get("emoji", "🐾"), size=32),
        )
    role = str(data.get("role", "")).strip()
    role_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=999,
        bgcolor=THEME["DETAIL_BG"],
        content=ft.Text(role or "藝素村夥伴", size=12, weight=ft.FontWeight.W_800,
                        color=THEME["ANIMAL_ROLE"]),
    )
    return interactive_card(
        padding=16,
        border_radius=12,
        tooltip=f"{name} 詳細介紹",
        on_click=lambda _event, pet=name: on_click(pet) if on_click else None,
        content=ft.Row(
            controls=[
                portrait_preview,
                ft.Column(
                    controls=[
                        ft.Text(name, size=19, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        role_badge,
                        ft.Text(summary or "一起認識這位藝素村小夥伴。",
                                size=13, color=THEME["BODY"]),
                    ],
                    spacing=6, expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=THEME["MUTED"]),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def get_animals_view(
    page: ft.Page,
    on_animal_click: Callable[[str], None] | None = None,
) -> ft.Column:
    """Build the customer-facing animal mode view."""
    animals = load_animals_db_dynamic()
    animal_controls: list[ft.Control]
    if animals:
        animal_controls = [animal_card(name, data, on_animal_click) for name, data in animals.items()]
    else:
        animal_controls = [
            interactive_card(
                padding=22,
                border_radius=12,
                content=ft.Column(
                    controls=[
                        ft.Text("目前尚無動物介紹", size=17, weight=ft.FontWeight.W_900,
                                color=THEME["TITLE"]),
                        ft.Text("請稍後再回來看看藝素村的小夥伴。", size=13, color=THEME["BODY"]),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        ]
    return ft.Column(
        controls=[
            section_label(SECTION_ICONS["animal_section"], "認識動物"),
            ft.Text("點擊卡片，打開牠的介紹卡片。", size=14, color=THEME["BODY"]),
            ft.Column(
                controls=animal_controls,
                spacing=12,
            ),
        ],
        spacing=14, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
