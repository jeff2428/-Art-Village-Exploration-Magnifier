from __future__ import annotations

import flet as ft

FONT_XXS = 10
FONT_XS = 11
FONT_SM = 13
FONT_MD = 15
FONT_LG = 19
FONT_XL = 24
FONT_XXL = 32
FONT_HERO = 36

SHADOW_CARD_PROPS = {"blur_radius": 16, "offset": ft.Offset(0, 8)}
SHADOW_CARD2_PROPS = {"blur_radius": 14, "offset": ft.Offset(0, 8)}
SHADOW_GALLERY_PROPS = {"blur_radius": 10, "offset": ft.Offset(0, 5)}


def _theme(is_dark: bool) -> dict[str, str]:
    if is_dark:
        return {
            "PAGE_BG": "#1a1512",
            "CARD_BG": "#2c241e",
            "CARD_BORDER": "#3d322a",
            "CARD_BORDER_ALT": "#4a3e34",
            "TITLE": "#ede0c8",
            "BODY": "#c4b59a",
            "BODY_DARK": "#d4c4a8",
            "MUTED": "#8a7a68",
            "ACCENT": "#c99a5a",
            "GREEN": "#4a9c6e",
            "WHITE": "#2c241e",
            "SHADOW_CARD": "#0000001a",
            "SHADOW_CARD2": "#00000014",
            "SHADOW_GALLERY": "#00000012",
            "SHADOW_CAMERA": "#0000002e",
            "DETAIL_BG": "#2f2720",
            "DETAIL_BORDER": "#40362e",
            "WARNING_BG": "#3d3208",
            "WARNING_TEXT": "#ffd54f",
            "ANIMAL_ROLE": "#c9a87c",
            "CAMERA_BG": "#0f0b09",
            "CAMERA_BORDER": "#1c1410",
            "CAMERA_INNER": "#0a0d0c",
            "ORGAN_BG": "#2f2720",
            "PERENUAL_BG": "#3a3028",
            "CONFIDENCE_BG": "#5a4532",
            "DETAIL_TEXT": "#a8947e",
            "ILLUSTRATION_DECORATIVE": "#5a4a3a",
            "LEAF_GREEN": "#5a8a5a",
            "BIRD_ACCENT": "#8a7a5a",
        }
    return {
        "PAGE_BG": "#f3efd9",
        "CARD_BG": "#fffdf4",
        "CARD_BORDER": "#dccfc0",
        "CARD_BORDER_ALT": "#d7c8b9",
        "TITLE": "#3d2a21",
        "BODY": "#6d5140",
        "BODY_DARK": "#5c4032",
        "MUTED": "#8a6a54",
        "ACCENT": "#8a5a22",
        "GREEN": "#2f7d51",
        "WHITE": "#ffffff",
        "SHADOW_CARD": "#2b130814",
        "SHADOW_CARD2": "#2b130812",
        "SHADOW_GALLERY": "#2b130810",
        "SHADOW_CAMERA": "#442f2529",
        "DETAIL_BG": "#f7f0df",
        "DETAIL_BORDER": "#dfd0bd",
        "WARNING_BG": "#fff3cd",
        "WARNING_TEXT": "#856404",
        "ANIMAL_ROLE": "#7a4b38",
        "CAMERA_BG": "#4d3026",
        "CAMERA_BORDER": "#2b160f",
        "CAMERA_INNER": "#0f1512",
        "ORGAN_BG": "#fff8e8",
        "PERENUAL_BG": "#efe4d1",
        "CONFIDENCE_BG": "#e8bc96",
        "DETAIL_TEXT": "#7a6657",
        "ILLUSTRATION_DECORATIVE": "#8a7a6a",
        "LEAF_GREEN": "#6a9a5a",
        "BIRD_ACCENT": "#5a7a9a",
    }


THEME = _theme(is_dark=False)


def apply_theme(is_dark: bool) -> None:
    THEME.clear()
    THEME.update(_theme(is_dark))


def border_all(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
    return ft.Container(
        bgcolor=THEME["CARD_BG"],
        border_radius=16,
        padding=padding,
        border=border_all(1, THEME["CARD_BORDER"]),
        shadow=ft.BoxShadow(blur_radius=16, color=THEME["SHADOW_CARD"], offset=ft.Offset(0, 8)),
        content=content,
    )


def card_shadow(
    blur_radius: int = 10,
    color: str | None = None,
    offset: ft.Offset | None = None,
) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=blur_radius,
        color=color or THEME["SHADOW_GALLERY"],
        offset=offset or ft.Offset(0, 5),
    )


def section_label(icon: str, text: str) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Text(icon, size=24),
            ft.Text(text, size=24, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )
