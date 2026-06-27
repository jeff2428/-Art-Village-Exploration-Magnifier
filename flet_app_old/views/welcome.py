from __future__ import annotations

from typing import Any

import flet as ft
from build_config import CONTENT_MAX_WIDTH, CONTENT_MIN_PADDING
from components.illustrations import (
    build_welcome_decoration,
    paper_texture_container,
)
from ui_theme import THEME, border_all


def _feature_line(text: str) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Text("•", size=20, color=THEME["BODY"], weight=ft.FontWeight.W_900),
            ft.Text(text, size=15, color=THEME["BODY"]),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def build_welcome_screen(page: ft.Page) -> ft.Container:
    welcome = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        padding=ft.Padding.symmetric(vertical=60, horizontal=24),
        content=paper_texture_container(
            ft.Column(
                controls=[
                    build_welcome_decoration(),
                    ft.Container(height=8),
                    ft.Container(
                        width=76,
                        height=76,
                        border_radius=999,
                        border=border_all(3, THEME["TITLE"]),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("探", size=36, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                    ),
                    ft.Text("探險放大鏡", size=32, weight=ft.FontWeight.W_900,
                           text_align=ft.TextAlign.CENTER, color=THEME["TITLE"]),
                    ft.Text("藝素村的自然探險工具", size=18, weight=ft.FontWeight.W_700,
                           text_align=ft.TextAlign.CENTER, color=THEME["BODY_DARK"]),
                    ft.Container(height=16),
                    _feature_line("拍攝並辨識植物物種"),
                    _feature_line("認識村里的動物朋友"),
                    _feature_line("建立你的探險圖鑑"),
                    ft.Container(height=24),
                    ft.Text("使用相機功能需要瀏覽器授權，", size=13, color=THEME["MUTED"]),
                    ft.Text("請確保使用 HTTPS 或 localhost 網址", size=13, color=THEME["MUTED"]),
                    ft.Container(height=32),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=0,
        ),
    )
    return welcome


def build_start_button(on_click: Any = None) -> ft.ElevatedButton:
    """Builds the start exploration button."""
    return ft.ElevatedButton(
        "開始探險",
        on_click=on_click,
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=40, vertical=18),
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.W_900),
            bgcolor=THEME["ACCENT"],
            color=THEME["WHITE"],
        ),
    )


def build_loading_carousel() -> tuple[ft.Container, ft.Text, ft.Text]:
    """Builds loading carousel with emoji cycling and message. Returns (container, emoji_text, message_text)."""
    loading_emoji = ft.Text("🔍", size=56, text_align=ft.TextAlign.CENTER)
    loading_message = ft.Text(
        "正在呼喚小夥伴們...", size=16, color=THEME["BODY"], weight=ft.FontWeight.W_700
    )
    carousel = ft.Container(
        height=170,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            controls=[
                ft.Container(height=40),
                loading_emoji,
                ft.Container(height=12),
                ft.ProgressRing(width=36, height=36, stroke_width=4, color=THEME["ACCENT"]),
                ft.Container(height=16),
                loading_message,
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return carousel, loading_emoji, loading_message
