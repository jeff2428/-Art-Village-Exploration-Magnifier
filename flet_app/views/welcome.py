from __future__ import annotations

import flet as ft
from build_config import CONTENT_MAX_WIDTH, CONTENT_MIN_PADDING
from ui_theme import THEME


def build_welcome_screen(page: ft.Page) -> ft.Container:
    """Builds welcome screen container with emoji, title, description, and start button."""
    welcome = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        padding=ft.Padding.symmetric(vertical=60, horizontal=24),
        content=ft.Column(
            controls=[
                ft.Text("🔍", size=80, text_align=ft.TextAlign.CENTER),
                ft.Text("探險放大鏡", size=32, weight=ft.FontWeight.W_900,
                       text_align=ft.TextAlign.CENTER, color=THEME["TITLE"]),
                ft.Text("藝素村的自然探險工具", size=18, weight=ft.FontWeight.W_700,
                       text_align=ft.TextAlign.CENTER, color=THEME["BODY_DARK"]),
                ft.Container(height=16),
                ft.Text("🌿 拍攝並辨識植物物種", size=15, color=THEME["BODY"]),
                ft.Text("🐾 認識村里的動物朋友", size=15, color=THEME["BODY"]),
                ft.Text("🎒 建立你的探險圖鑑", size=15, color=THEME["BODY"]),
                ft.Container(height=24),
                ft.Text("使用相機功能需要瀏覽器授權，", size=13, color=THEME["MUTED"]),
                ft.Text("請確保使用 HTTPS 或 localhost 網址", size=13, color=THEME["MUTED"]),
                ft.Container(height=32),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return welcome


def build_start_button() -> ft.ElevatedButton:
    """Builds the start exploration button."""
    return ft.ElevatedButton(
        "開始探險",
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
        expand=True,
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
