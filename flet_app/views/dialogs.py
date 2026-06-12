from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft
from components.illustrations import PAW_PRINTS
from plant_api import (
    PLANT_ORGAN_OPTIONS,
    UNKNOWN_METADATA,
    confidence_text,
)
from pokedex_manager import DEFAULT_ANIMALS, load_animals_db_dynamic
from ui_theme import THEME, border_all, soft_card


def close_dialog(page: ft.Page, _event: ft.ControlEvent | None = None) -> None:
    """Close the current dialog. From main.py lines 462-467."""
    try:
        page.pop_dialog()
    except (AttributeError, RuntimeError):
        pass
    page.update()


def show_recognition_loading_card(page: ft.Page, state) -> None:
    """Show recognition loading dialog. From main.py lines 469-489."""
    state.recognition_loading_visible = True
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("辨識中", size=24, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
            content=soft_card(
                ft.Column(
                    controls=[
                        ft.ProgressRing(width=34, height=34, stroke_width=4, color=THEME["ACCENT"]),
                        ft.Text("正在分析拍攝內容", size=16, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text("請稍候，完成後會自動顯示辨識結果卡片。", size=13, color=THEME["BODY"]),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
            ),
        )
    )
    page.update()


def close_recognition_loading_card(page: ft.Page, state, update_page: bool = True) -> None:
    """Close recognition loading dialog. From main.py lines 491-497."""
    if not state.recognition_loading_visible:
        return
    page.pop_dialog()
    state.recognition_loading_visible = False
    if update_page:
        page.update()


def show_animal_card(
    page: ft.Page,
    state,
    status_text: ft.Text,
    add_animal_callback: Callable[[str], None],
    name: str,
) -> None:
    """Show detailed animal card dialog. From main.py lines 567-639."""
    try:
        animals_db = load_animals_db_dynamic()
        data = animals_db.get(name) or DEFAULT_ANIMALS.get(name)
        if not data:
            status_text.value = f"找不到動物「{name}」的資料"
            page.update()
            return
        add_animal_callback(name)
        portrait_src = data.get("portrait", "")
        photos = data.get("photos", []) or []
        portrait_control: ft.Control
        if portrait_src:
            portrait_control = ft.Container(
                height=200, border_radius=14, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(src=portrait_src, fit=ft.BoxFit.COVER, width=340, height=200),
            )
        else:
            portrait_control = ft.Container(
                height=140, border_radius=14, alignment=ft.Alignment(0, 0),
                bgcolor=THEME["PERENUAL_BG"],
                border=border_all(1, THEME["DETAIL_BORDER"]),
                content=ft.Text(data.get("emoji", PAW_PRINTS), size=56),
            )
        photo_controls: list[ft.Control] = []
        if photos:
            photo_thumbs: list[ft.Control] = [
                ft.Container(
                    width=64, height=64, border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Image(src=photo, fit=ft.BoxFit.COVER),
                )
                for photo in photos[:6]
            ]
            photo_controls = [
                ft.Text("生活照", size=12, color=THEME["MUTED"], weight=ft.FontWeight.W_900),
                ft.Row(controls=photo_thumbs, spacing=6, wrap=True),
            ]
            if len(photos) > 6:
                photo_controls.append(ft.Text(f"+{len(photos) - 6} 張更多照片", size=11, color=THEME["MUTED"]))
        dialog_content_height = max(420, min(520, round((page.height or 760) * 0.58)))
        page.show_dialog(
            ft.AlertDialog(
                modal=True, scrollable=True,
                title=ft.Text(f"{data.get('emoji', PAW_PRINTS)} {name}", size=24, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                content=ft.Container(
                    width=360, height=dialog_content_height,
                    content=soft_card(
                        ft.Column(
                            controls=[
                                portrait_control, *photo_controls,
                                ft.Container(height=8),
                                ft.Text(data.get("role", ""), size=14, color=THEME["ANIMAL_ROLE"],
                                       weight=ft.FontWeight.W_800),
                                ft.Text(data.get("desc", ""), size=15, color=THEME["TITLE"]),
                                ft.Container(
                                    padding=ft.Padding.only(top=8),
                                    content=ft.Text("已加入探險圖鑑", size=13, color=THEME["GREEN"],
                                                   weight=ft.FontWeight.W_800),
                                ),
                            ],
                            spacing=8, scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=14,
                    ),
                ),
                actions=[ft.TextButton("關閉", on_click=lambda e: close_dialog(page, e))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()
    except Exception as e:
        status_text.value = f"無法打開動物卡片：{e}"
        page.update()


def show_plant_card(
    page: ft.Page,
    state,
    status_text: ft.Text,
    name: str,
    data: dict[str, Any],
) -> None:
    """Show detailed plant card dialog. From main.py lines 641-795 (full original)."""
    confidence = data.get("confidence", 0)
    is_low_confidence = data.get("is_low_confidence", False)
    alternatives = data.get("alternatives") or []
    aliases = data.get("aliases") or []
    captured_image = data.get("captured_image") or {}
    toxicity = data.get("toxicity") or UNKNOWN_METADATA["toxicity"]
    invasive = data.get("invasive") or UNKNOWN_METADATA["invasive"]
    care = {key: value for key, value in (data.get("care") or {}).items() if value}
    metadata_source = data.get("metadata_source") or "PlantNet"
    metadata_status = data.get("metadata_status") or "not_requested"
    worker_timing = data.get("worker_timing") or {}
    organ_label = data.get("organ_label") or PLANT_ORGAN_OPTIONS.get(data.get("organ", "auto"), "自動")

    def detail_text(value: str, *, size: int = 13, color: str = THEME["BODY_DARK"],
                    weight: ft.FontWeight | None = None) -> ft.Text:
        return ft.Text(value, size=size, color=color, weight=weight, selectable=True)

    def info_chip(label: str, value: str, detail: str = "") -> ft.Control:
        return ft.Container(
            padding=10, border_radius=10,
            bgcolor=THEME["DETAIL_BG"],
            border=border_all(1, THEME["DETAIL_BORDER"]),
            content=ft.Column(
                controls=[
                    ft.Text(label, size=11, color=THEME["ACCENT"], weight=ft.FontWeight.W_900),
                    ft.Text(value, size=13, color=THEME["TITLE"], weight=ft.FontWeight.W_800),
                    ft.Text(detail, size=10, color=THEME["DETAIL_TEXT"]) if detail else ft.Container(),
                ],
                spacing=2,
            ),
        )

    image_src = captured_image.get("src", "")
    image_banner: ft.Control
    if image_src:
        image_banner = ft.Container(
            height=170, border_radius=14, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=THEME["PERENUAL_BG"],
            content=ft.Image(src=image_src, fit=ft.BoxFit.COVER, width=340, height=170),
        )
    else:
        image_banner = ft.Container(
            height=112, border_radius=14, alignment=ft.Alignment(0, 0),
            bgcolor=THEME["PERENUAL_BG"],
            border=border_all(1, THEME["DETAIL_BORDER"]),
            content=ft.Text(
                captured_image.get("label") or "尚無拍攝照片",
                size=13, color=THEME["DETAIL_TEXT"], weight=ft.FontWeight.W_800,
            ),
        )

    warning_text: ft.Control = ft.Container()
    if is_low_confidence and confidence > 0:
        warning_text = ft.Container(
            padding=8, margin=ft.Margin.only(bottom=8),
            bgcolor=THEME["WARNING_BG"], border_radius=8,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_OUTLINED, size=16, color=THEME["WARNING_TEXT"]),
                    ft.Text(f"置信度僅 {confidence}%，建議實地確認物種",
                           size=13, color=THEME["WARNING_TEXT"], weight=ft.FontWeight.W_700),
                ],
                spacing=6,
            ),
        )

    alternative_controls: list[ft.Control] = []
    if alternatives:
        alternative_controls = [
            ft.Text("備選辨識", size=14, color=THEME["TITLE"], weight=ft.FontWeight.W_900),
            *[
                ft.Container(
                    padding=8, border_radius=10, bgcolor=THEME["DETAIL_BG"],
                    content=                    ft.Text(f"{candidate.get('zh_name', '?')} · {candidate.get('confidence', 0)}%",
                                   size=12, color=THEME["BODY_DARK"]),
                )
                for candidate in alternatives
            ],
        ]

    alias_controls: list[ft.Control] = []
    if aliases:
        alias_controls = [
            ft.Text("別名", size=12, color=THEME["ACCENT"], weight=ft.FontWeight.W_900),
            ft.Text("、".join(aliases), size=13, color=THEME["BODY_DARK"]),
        ]

    metadata_controls: list[ft.Control] = [
        info_chip("拍攝部位", organ_label),
        info_chip("毒性", toxicity.get("label", "資料待確認"), toxicity.get("detail", "")),
        info_chip("外來種", invasive.get("label", "資料待確認"), invasive.get("detail", "")),
    ]
    care_controls: list[ft.Control] = []
    if care:
        care_controls = [
            ft.Text("Perenual 植物資料", size=14, color=THEME["TITLE"], weight=ft.FontWeight.W_900),
            ft.Row(
                controls=[info_chip(label, str(value)) for label, value in care.items()],
                spacing=8, wrap=True,
            ),
        ]
    metadata_note = "Perenual 資料背景載入中" if metadata_status == "pending" else f"資料來源：{metadata_source}"
    timing_note = ""
    if worker_timing.get("total_ms") is not None:
        timing_note = (f"端點耗時：{worker_timing.get('total_ms')}ms "
                      f"（PlantNet {worker_timing.get('plantnet_ms', 'N/A')}ms）")
    dialog_content_height = max(420, min(520, round((page.height or 760) * 0.58)))
    plant_detail_content = ft.Column(
        controls=[
            image_banner, warning_text,
            ft.Row(
                controls=[
                    ft.Text(data.get("zh_name", name), size=22, color=THEME["TITLE"],
                           weight=ft.FontWeight.W_900, expand=True),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        border_radius=999, bgcolor=THEME["CONFIDENCE_BG"],
                        content=ft.Text(f"{confidence}%", size=13, color=THEME["TITLE"],
                                      weight=ft.FontWeight.W_900),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            detail_text(data.get("eng_name") or "N/A", size=14, color=THEME["BODY"],
                       weight=ft.FontWeight.W_800),
            detail_text(data.get("sci_name") or "", size=12, color=THEME["MUTED"]),
            *alias_controls,
            ft.Column(controls=metadata_controls, spacing=8),
            ft.Text(data.get("desc", ""), size=14, color=THEME["TITLE"]),
            *care_controls,
            ft.Text(metadata_note, size=11, color=THEME["MUTED"]),
            ft.Text(timing_note, size=11, color=THEME["MUTED"]) if timing_note else ft.Container(),
            ft.Text(confidence_text(data), size=13, color=THEME["BODY"]),
            *alternative_controls,
            ft.Container(
                padding=ft.Padding.only(bottom=12),
                content=ft.Text("已加入探險圖鑑", size=13, color=THEME["GREEN"], weight=ft.FontWeight.W_800),
            ),
        ],
        spacing=10, scroll=ft.ScrollMode.AUTO,
    )
    page.show_dialog(
        ft.AlertDialog(
            modal=True, scrollable=True,
            title=ft.Text(f"{data.get('emoji', '🌿')} {name}", size=24, weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
            content=ft.Container(
                width=360, height=dialog_content_height,
                content=soft_card(plant_detail_content, padding=14),
            ),
            actions=[ft.TextButton("關閉", on_click=lambda e: close_dialog(page, e))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )
    page.update()
