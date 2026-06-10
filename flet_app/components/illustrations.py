from __future__ import annotations

import flet as ft
from app_types import AppMode
from ui_theme import THEME, border_all

TAIWAN_BLUE_MAGPIE = "\U0001f426"
TAIWAN_LILY = "\U0001f33b"
TREE_FROG = "\U0001f438"
CICADA = "\U0001f997"
SHELL_GINGER_LEAF = "\U0001f33f"
BUTTERFLY = "\U0001f98b"
CAMPHOR_TREE = "\U0001f333"
MOUNTAIN = "\U0001f3d4\ufe0f"
MAGNIFYING_GLASS = "\U0001f50d"
BACKPACK = "\U0001f392"
CHERRY_BLOSSOM = "\U0001f338"
LEAF_FLUTTER = "\U0001f343"
PAW_PRINTS = "\U0001f43e"
DOG = "\U0001f415"
BOOK = "\U0001f4d6"

MODE_ICONS: dict[AppMode, str] = {
    AppMode.LANDING: MAGNIFYING_GLASS,
    AppMode.PLANT: SHELL_GINGER_LEAF,
    AppMode.ANIMAL: TAIWAN_BLUE_MAGPIE,
}

LOADING_EMOJI_CYCLE: list[str] = [
    MAGNIFYING_GLASS,
    SHELL_GINGER_LEAF,
    PAW_PRINTS,
    BACKPACK,
    CHERRY_BLOSSOM,
    CAMPHOR_TREE,
    DOG,
]

SECTION_ICONS: dict[str, str] = {
    "gallery_header": BOOK,
    "gallery_empty": MAGNIFYING_GLASS,
    "animal_section": PAW_PRINTS,
    "plant_section": SHELL_GINGER_LEAF,
}

STATUS_PREFIX: dict[str, str] = {
    "ok": "\u2705 ",
    "warn": "\u26a0\ufe0f ",
    "err": "\u274c ",
    "info": "",
}


def paper_texture_container(
    content: ft.Control,
    *,
    padding: int = 0,
    border_radius: int = 0,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                THEME["CARD_BG"],
                _lighten(THEME["CARD_BG"], 0.02),
                THEME["CARD_BG"],
            ],
        ),
    )


def _lighten(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def nature_border_container(
    content: ft.Control,
    *,
    width: int | None = None,
    height: int | None = None,
    border_radius: int = 16,
) -> ft.Container:
    return ft.Container(
        width=width,
        height=height,
        content=content,
        border_radius=border_radius,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, 0),
            end=ft.Alignment(0, 1),
            colors=[
                THEME["CARD_BG"],
                _lighten(THEME["CARD_BG"], 0.015),
            ],
        ),
        border=border_all(1, THEME["CARD_BORDER"]),
    )


def build_welcome_decoration() -> ft.Row:
    return ft.Row(
        controls=[
            ft.Text(SHELL_GINGER_LEAF, size=16, opacity=0.3),
            ft.Text(TAIWAN_LILY, size=20, opacity=0.25),
            ft.Text(LEAF_FLUTTER, size=14, opacity=0.3),
            ft.Text(BUTTERFLY, size=18, opacity=0.2),
            ft.Text(CHERRY_BLOSSOM, size=16, opacity=0.25),
        ],
        spacing=16,
        alignment=ft.MainAxisAlignment.CENTER,
    )
