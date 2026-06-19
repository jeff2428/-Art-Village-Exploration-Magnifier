"""Shared control factories used by main.py entry point."""

from __future__ import annotations

import asyncio
from typing import Any

import flet as ft
from app_state import AppState


def create_shared_controls(state: AppState) -> tuple[ft.Text, ft.ProgressRing]:
    """Create the shared status text and busy ring controls."""
    from ui_theme import THEME

    status = ft.Text(
        "", size=13, color=THEME["BODY"], weight=ft.FontWeight.W_800,
        text_align=ft.TextAlign.CENTER, expand=True,
    )
    busy_ring = ft.ProgressRing(
        width=22, height=22, stroke_width=3, visible=False, color=THEME["ACCENT"]
    )
    return status, busy_ring


def create_background_task_factory(page: ft.Page, state: AppState) -> Any:
    """Return a function that wraps coroutines as background tasks."""

    def create(coro: Any) -> None:
        run_task = getattr(page, "run_task", None)
        if callable(run_task):
            async def runner() -> None:
                await coro
            run_task(runner)
            return
        task = asyncio.create_task(coro)
        state.background_tasks.add(task)
        task.add_done_callback(lambda t: state.background_tasks.discard(t))

    return create


def organ_mode_button() -> ft.SegmentedButton:
    """Create the plant organ segmentation button."""
    from plant_api import PLANT_ORGAN_ICONS

    options = ["auto", "leaf", "flower", "fruit", "bark"]
    labels = {"auto": "\\u81ea\\u52d5", "leaf": "\\u8449", "flower": "\\u82b1", "fruit": "\\u679c", "bark": "\\u6a39\\u76ae"}

    return ft.SegmentedButton(
        selected=["auto"],
        allow_multiple_selection=False,
        on_change=lambda _e: None,
        segments=[
            ft.Segment(
                value=v,
                icon=PLANT_ORGAN_ICONS.get(v),
                label=ft.Text(labels.get(v, v), size=12),
            )
            for v in options
        ],
    )
