from __future__ import annotations

from collections.abc import Callable
from typing import Any

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
            "PAGE_BG": "#121816",
            "CARD_BG": "#202824CC",
            "CARD_BORDER": "#314238",
            "CARD_BORDER_ALT": "#3b5146",
            "TITLE": "#edf3e8",
            "BODY": "#c2d3c6",
            "BODY_DARK": "#d6e2d6",
            "MUTED": "#8fa699",
            "ACCENT": "#6fbe86",
            "ACCENT_SECONDARY": "#72a9d6",
            "GREEN": "#6fbe86",
            "WHITE": "#2c241e",
            "SHADOW_CARD": "#00000022",
            "SHADOW_CARD2": "#00000018",
            "SHADOW_GALLERY": "#00000016",
            "SHADOW_CAMERA": "#0000002e",
            "DETAIL_BG": "#26312c",
            "DETAIL_BORDER": "#3a5145",
            "WARNING_BG": "#3d3208",
            "WARNING_TEXT": "#ffd54f",
            "ANIMAL_ROLE": "#89b8df",
            "CAMERA_BG": "#0f0b09",
            "CAMERA_BORDER": "#1c1410",
            "CAMERA_INNER": "#0a0d0c",
            "ORGAN_BG": "#26312c",
            "PERENUAL_BG": "#2d3a35",
            "CONFIDENCE_BG": "#335943",
            "DETAIL_TEXT": "#9fb3a7",
            "ILLUSTRATION_DECORATIVE": "#536b5e",
            "LEAF_GREEN": "#6fbe86",
            "BIRD_ACCENT": "#72a9d6",
        }
    return {
        "PAGE_BG": "#eef5e9",
        "CARD_BG": "#fffdf7E6",
        "CARD_BORDER": "#d6e1cf",
        "CARD_BORDER_ALT": "#c7d9ce",
        "TITLE": "#24342a",
        "BODY": "#516458",
        "BODY_DARK": "#3f5247",
        "MUTED": "#74897b",
        "ACCENT": "#2f7d51",
        "ACCENT_SECONDARY": "#3f6f8f",
        "GREEN": "#2f7d51",
        "WHITE": "#ffffff",
        "SHADOW_CARD": "#163c2914",
        "SHADOW_CARD2": "#163c2912",
        "SHADOW_GALLERY": "#163c2910",
        "SHADOW_CAMERA": "#442f2529",
        "DETAIL_BG": "#f3f8ef",
        "DETAIL_BORDER": "#d2dfcf",
        "WARNING_BG": "#fff3cd",
        "WARNING_TEXT": "#856404",
        "ANIMAL_ROLE": "#3f6f8f",
        "CAMERA_BG": "#4d3026",
        "CAMERA_BORDER": "#2b160f",
        "CAMERA_INNER": "#0f1512",
        "ORGAN_BG": "#f6fbf2",
        "PERENUAL_BG": "#e7f1e5",
        "CONFIDENCE_BG": "#cde8d3",
        "DETAIL_TEXT": "#66776d",
        "ILLUSTRATION_DECORATIVE": "#819282",
        "LEAF_GREEN": "#6a9a5a",
        "BIRD_ACCENT": "#3f6f8f",
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
        blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
        content=content,
    )


def interactive_card(
    content: ft.Control,
    *,
    padding: int = 14,
    border_radius: int = 12,
    tooltip: str | None = None,
    on_click: Callable[..., Any] | None = None,
    on_long_press: Callable[..., Any] | None = None,
) -> ft.Container:
    card = ft.Container(
        bgcolor=THEME["CARD_BG"],
        border_radius=border_radius,
        padding=padding,
        alignment=ft.Alignment(0, 0),
        border=border_all(1, THEME["CARD_BORDER_ALT"]),
        shadow=card_shadow(),
        blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
        animate=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        animate_opacity=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
        tooltip=tooltip,
        on_click=on_click,
        on_long_press=on_long_press,
        content=content,
    )
    card.on_hover = lambda event: apply_card_hover(card, event)
    return card


def apply_card_hover(card: ft.Container, event: ft.ControlEvent) -> None:
    is_hovered = event.data == "true"
    card.scale = 1.025 if is_hovered else 1.0
    card.shadow = [
        card_shadow(
            blur_radius=16 if is_hovered else 10,
            offset=ft.Offset(0, 7 if is_hovered else 5),
        ),
    ]
    card.update()


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
