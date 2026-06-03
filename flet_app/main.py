from __future__ import annotations

import asyncio
import os
from typing import Any

import flet as ft

try:
    import flet_camera as fc
except ImportError:
    fc = None

from app_state import AppState
from app_types import AppMode
from build_config import CONTENT_MAX_WIDTH, CONTENT_MIN_PADDING
from camera_utils import (
    MIN_CAMERA_ZOOM,
)
from components.illustrations import LOADING_EMOJI_CYCLE, MODE_ICONS
from plant_api import PLANT_ORGAN_ICONS, PLANT_ORGAN_OPTIONS
from pokedex_manager import (
    clear_legacy_snapshot_cache,
    load_cached_pokedex,
    load_dark_mode_preference,
    save_dark_mode_preference,
)
from services.camera_manager import CameraManager
from services.recognition import RecognitionService
from services.storage import GalleryService
from ui_theme import FONT_HERO, THEME, apply_theme, soft_card
from views import animal_view as av
from views import dialogs as dv
from views import gallery as gv
from views import plant_view as pv
from views import welcome as wv


def status_msg(text: str, level: str = "info") -> str:
    prefix = {"ok": "\u2705 ", "warn": "\u26a0\ufe0f ", "err": "\u274c ", "info": ""}
    return f"{prefix.get(level, '')}{text}"


def mark_explorer_ready() -> None:
    try:
        from js import window  # type: ignore
        window.__artVillageReady = True
    except Exception:
        pass


def mark_load_timing(name: str) -> None:
    try:
        from js import performance  # type: ignore
        performance.mark(name)
    except Exception:
        pass


def report_performance(page: ft.Page) -> None:
    try:
        page.run_js("""
        try {
          const marks = performance.getEntriesByType("mark");
          const measures = performance.getEntriesByType("measure");
          console.log("\ud83d\udd0d \u63a2\u96aa\u653e\u5927\u93e1\u6548\u80fd\u5831\u544a");
          marks.forEach(m => console.log("  Mark: " + m.name + " @ " + m.startTime.toFixed(0) + "ms"));
          measures.forEach(m => console.log("  " + m.name + ": " + m.duration.toFixed(0) + "ms"));
        } catch (e) {
          console.warn("\u6548\u80fd\u5831\u544a\u5931\u6557:", e);
        }
        """)
    except Exception:
        pass


async def main(page: ft.Page) -> None:
    try:
        await run_app(page)
    except Exception as error:
        page.clean()
        page.bgcolor = THEME["PAGE_BG"]
        page.add(
            ft.Container(
                padding=24,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    [
                        ft.Text("\u63a2\u96aa\u653e\u5927\u93e1\u8f09\u5165\u5931\u6557", size=26,
                               weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text(str(error), size=14, color=THEME["BODY_DARK"], selectable=True),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        page.update()


async def run_app(page: ft.Page) -> None:
    page.title = "\u85dd\u7d20\u6751\u63a2\u96aa\u653e\u5927\u93e1"
    state = AppState(page=page)
    state.pokedex = await load_cached_pokedex()
    state.is_dark_mode = await load_dark_mode_preference()
    apply_theme(state.is_dark_mode)
    clear_legacy_snapshot_cache()
    state.zoom_level = MIN_CAMERA_ZOOM

    page.theme_mode = ft.ThemeMode.DARK if state.is_dark_mode else ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor = THEME["PAGE_BG"]
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Shared controls used by multiple views
    status = ft.Text("", size=13, color=THEME["BODY"], weight=ft.FontWeight.W_800,
                     text_align=ft.TextAlign.CENTER, expand=True)
    busy_ring = ft.ProgressRing(width=22, height=22, stroke_width=3, visible=False, color=THEME["ACCENT"])
    restart_camera_button = ft.TextButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.VIDEOCAM, size=16),
                ft.Text("\u91cd\u65b0\u555f\u52d5\u76f8\u6a5f"),
            ],
            spacing=4,
        ),
        tooltip="\u91cd\u65b0\u8acb\u6c42\u76f8\u6a5f\u6b0a\u9650\u4e26\u555f\u52d5\u93e1\u982d",
    )

    # Mode toggle shared state
    selected_mode: dict[str, str] = {"value": "plant"}

    # Organ mode selector
    organ_options = ["auto", "leaf", "flower", "fruit", "bark"]
    organ_mode = ft.SegmentedButton(
        selected={"auto"},
        show_selected_foreground=False,
        allow_multiple_selection=False,
        on_change=lambda _e: None,
        segments=[
            ft.Segment(
                value=v,
                label=ft.Text(
                    f"{PLANT_ORGAN_ICONS.get(v, '')} {PLANT_ORGAN_OPTIONS.get(v, v)}",
                    size=12,
                ),
            )
            for v in organ_options
        ],
    )

    def selected_organ_value() -> str:
        if organ_mode.selected:
            return list(organ_mode.selected)[0]
        return "auto"

    def create_background_task(coro: Any) -> None:
        task = asyncio.create_task(coro)
        state.background_tasks.add(task)
        task.add_done_callback(lambda t: state.background_tasks.discard(t))

    # Wire gallery card click routing
    def show_gallery_card(name: str, data: dict[str, Any]) -> None:
        if data.get("type") == "animal":
            dv.show_animal_card(page, state, status, gallery_service.add_animal, name)
        else:
            dv.show_plant_card(page, state, status, name, data)

    # Gallery service
    gallery_service = GalleryService(
        page=page,
        state=state,
        status_text=status,
        create_background_task=create_background_task,
        show_gallery_card=show_gallery_card,
        close_dialog=lambda e: dv.close_dialog(page, e),
    )

    # Recognition service
    recognition_service = RecognitionService(
        page=page,
        state=state,
        status_text=status,
        create_background_task=create_background_task,
        mark_load_timing=mark_load_timing,
        initialize_camera=lambda: camera.initialize(),
        refresh_gallery=gallery_service.refresh,
    )

    # Capture result callback
    async def on_capture_result(plant: dict[str, Any]) -> None:
        gallery_service.add_plant(plant)
        dv.show_plant_card(page, state, status, plant["zh_name"], plant)
        if plant.get("metadata_status") == "pending":
            create_background_task(recognition_service.refresh_plant_metadata(plant))

    # Camera manager
    camera = CameraManager(
        page=page,
        state=state,
        status_text=status,
        busy_ring=busy_ring,
        on_capture_result=on_capture_result,
        create_background_task=create_background_task,
        get_selected_organ=selected_organ_value,
        is_plant_mode=lambda: selected_mode["value"] == "plant",
    )

    restart_camera_button.on_click = camera.initialize

    # Welcome screen
    welcome_screen = wv.build_welcome_screen(page)
    start_button = wv.build_start_button()
    loading_carousel, loading_emoji, loading_message = wv.build_loading_carousel()
    welcome_screen.content.controls.append(start_button)

    # Mode switching
    async def hide_camera_preview() -> None:
        state.camera_ready = False
        if state.camera is not None:
            try:
                await state.camera.pause_preview()
            except Exception:
                pass
        camera.camera_preview_slot.visible = False
        camera.camera_preview_slot.content = camera.camera_placeholder
        state.camera = None

    def restore_camera_preview() -> None:
        camera.camera_preview_slot.visible = True
        camera.camera_preview_slot.content = camera.camera_placeholder

    def build_mode_selector() -> ft.Row:
        def option(value: str, icon: str, label: str) -> ft.TextButton:
            is_active = selected_mode["value"] == value
            return ft.TextButton(
                content=ft.Column(
                    controls=[
                        ft.Text(icon, size=20 if is_active else 16),
                        ft.Text(label, size=13 if is_active else 12,
                               weight=ft.FontWeight.W_900 if is_active else ft.FontWeight.W_700,
                               color=THEME["ACCENT"] if is_active else THEME["BODY"]),
                    ],
                    spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda _e: set_mode(value),
            )
        return ft.Row(
            controls=[
                option("plant", MODE_ICONS[AppMode.PLANT], "\u690d\u7269"),
                option("animal", MODE_ICONS[AppMode.ANIMAL], "\u52d5\u7269"),
            ],
            spacing=24, alignment=ft.MainAxisAlignment.CENTER,
        )

    def set_mode(value: str) -> None:
        create_background_task(switch_mode(value))

    async def switch_mode(value: str) -> None:
        if value == selected_mode["value"]:
            return
        selected_mode["value"] = value
        if value == "animal":
            await hide_camera_preview()
            state.current_mode = AppMode.ANIMAL
        else:
            restore_camera_preview()
            state.current_mode = AppMode.PLANT
        if mode is not None:
            mode.content = build_mode_selector()
        _rebuild_visible_shell()

    def toggle_dark_mode(_event: ft.ControlEvent | None = None) -> None:
        state.is_dark_mode = not state.is_dark_mode
        apply_theme(state.is_dark_mode)
        page.theme_mode = ft.ThemeMode.DARK if state.is_dark_mode else ft.ThemeMode.LIGHT
        page.bgcolor = THEME["PAGE_BG"]
        create_background_task(save_dark_mode_preference(state.is_dark_mode))
        _rebuild_visible_shell()
        page.update()

    # Shell rebuild
    def _rebuild_visible_shell() -> None:
        for ctrl in [gallery_service.grid, gallery_service.gallery_empty_state, mode, content_area]:
            if ctrl is not None and ctrl.parent is not None:
                try:
                    if hasattr(ctrl.parent, "controls") and ctrl in ctrl.parent.controls:
                        ctrl.parent.controls.remove(ctrl)
                    elif hasattr(ctrl.parent, "content") and ctrl.parent.content == ctrl:
                        ctrl.parent.content = None
                except Exception:
                    pass
        toggle_icon = ft.Icons.DARK_MODE if not state.is_dark_mode else ft.Icons.LIGHT_MODE
        toggle_tip = "\u6df1\u8272\u6a21\u5f0f" if not state.is_dark_mode else "\u6dfa\u8272\u6a21\u5f0f"
        if mode is not None:
            mode.content = build_mode_selector()
        gallery_panel = gv.build_gallery_panel(
            gallery_service.grid, gallery_service.gallery_empty_state,
            on_clear=gallery_service.confirm_clear,
        )
        if selected_mode["value"] == "animal":
            new_content = av.get_animals_view(page)
        else:
            new_content = pv._build_plant_view(camera.magnifier_body, busy_ring, status,
                                                restart_camera_button, organ_mode)
        content_area.content = new_content
        shell.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("\u63a2\u96aa\u653e\u5927\u93e1", size=FONT_HERO,
                               weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                        ft.Text("\U0001f50d", size=FONT_HERO - 2),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=toggle_icon, icon_color=THEME["ACCENT"],
                            tooltip=toggle_tip, on_click=toggle_dark_mode,
                        ),
                    ],
                    spacing=6, alignment=ft.MainAxisAlignment.CENTER,
                ),
                soft_card(mode, padding=10),
                content_area,
                gallery_panel,
            ],
            spacing=18, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # Mode UI
    mode = ft.Container(content=build_mode_selector())
    content_area = ft.Container(padding=4)

    shell = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        visible=False,
    )
    page.add(welcome_screen, shell)

    # Start exploration
    async def start_exploration() -> None:
        start_button.text = "\u6e96\u5099\u4e2d..."
        start_button.disabled = True
        start_button.update()
        welcome_screen.content.controls[-1] = loading_carousel
        welcome_screen.update()
        emoji_cycle = LOADING_EMOJI_CYCLE
        messages = [
            "\u6b63\u5728\u547c\u559a\u5c0f\u5925\u4f34\u5011...",
            "\u7ffb\u958b\u690d\u7269\u5716\u9451\u4e2d...",
            "\u6e96\u5099\u63a2\u96aa\u88dd\u5099...",
            "\u555f\u52d5\u653e\u5927\u93e1...",
            "\u5373\u5c07\u51fa\u767c\uff01",
        ]
        for i in range(6):
            await asyncio.sleep(0.5)
            loading_emoji.value = emoji_cycle[i % len(emoji_cycle)]
            loading_message.value = messages[i] if i < len(messages) else "\u6e96\u5099\u5c31\u7e8c\uff01"
            loading_emoji.update()
            loading_message.update()

        async def build_shell() -> None:
            content_area.content = pv._build_plant_view(camera.magnifier_body, busy_ring, status,
                                                         restart_camera_button, organ_mode)
            camera.render_handle(update_page=False)
            if state.pokedex:
                gallery_service.refresh(update_page=False)

        await build_shell()
        welcome_screen.visible = False
        shell.visible = True
        page.update()

        await camera.initialize()
        report_performance(page)
        mark_explorer_ready()

    start_button.on_click = lambda _e: create_background_task(start_exploration())

    def _on_page_resize(_event: ft.ControlEvent | None = None) -> None:
        w = min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2)
        welcome_screen.width = w
        shell.width = w
        page.update()

    page.on_resize = _on_page_resize


if os.environ.get("FLET_SKIP_RUN") != "1":
    ft.run(main)
