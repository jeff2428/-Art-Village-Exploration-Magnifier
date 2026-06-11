from __future__ import annotations

import asyncio
import os
import traceback
from typing import Any, cast

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
from components.illustrations import MODE_ICONS
from plant_api import PLANT_ORGAN_ICONS, PLANT_ORGAN_OPTIONS
from pokedex_manager import (
    clear_legacy_snapshot_cache,
    flush_pokedex_save,
    load_cached_pokedex,
    load_dark_mode_preference,
    save_dark_mode_preference,
    sync_animals_from_worker,
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
    except (ImportError, AttributeError):
        pass


def mark_load_timing(name: str) -> None:
    try:
        from js import performance  # type: ignore
        performance.mark(name)
    except (ImportError, AttributeError):
        pass


def report_performance(page: ft.Page) -> None:
    try:
        run_js = getattr(page, "run_js", None)
        if not callable(run_js):
            return
        run_js("""
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
    except (AttributeError, TypeError):
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
                        ft.Text(
                            "".join(traceback.format_exception(error)),
                            size=14,
                            color=THEME["BODY_DARK"],
                            selectable=True,
                        ),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        page.update()
        mark_explorer_ready()


async def run_app(page: ft.Page) -> None:
    page.title = "\u85dd\u7d20\u6751\u63a2\u96aa\u653e\u5927\u93e1"

    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap",
        "Noto Sans TC": "https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap"
    }
    page.theme = ft.Theme(font_family="Noto Sans TC")

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
        selected=["auto"],
        allow_multiple_selection=False,
        on_change=lambda _e: None,
        segments=[
            ft.Segment(
                value=v,
                icon=PLANT_ORGAN_ICONS.get(v),
                label=ft.Text(
                    PLANT_ORGAN_OPTIONS.get(v, v),
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
        run_task = getattr(page, "run_task", None)
        if callable(run_task):
            async def runner() -> None:
                await coro

            run_task(runner)
            return
        task = asyncio.create_task(coro)
        state.background_tasks.add(task)
        task.add_done_callback(lambda t: state.background_tasks.discard(t))

    # Wire gallery card click routing
    def show_gallery_card(name: str, data: dict[str, Any]) -> None:
        if data.get("type") == "animal":
            dv.show_animal_card(page, state, status, gallery_service.add_animal, name)
        else:
            dv.show_plant_card(page, state, status, name, data)

    # Sync animals from worker
    async def _sync_animals() -> None:
        await sync_animals_from_worker()
        if selected_mode["value"] == "animal":
            _rebuild_visible_shell()
            page.update()

    create_background_task(_sync_animals())

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
        initialize_camera=lambda: camera.initialize(),  # type: ignore[has-type]
        refresh_gallery=gallery_service.refresh,
    )

    # Capture result callback
    async def on_capture_result(plant: dict[str, Any]) -> None:
        gallery_service.add_plant(plant)
        dv.show_plant_card(page, state, status, plant["zh_name"], plant)
        if plant.get("metadata_status") == "pending":
            create_background_task(recognition_service.refresh_plant_metadata(plant))

    # Camera manager
    camera: CameraManager = CameraManager(
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
    def on_start_click(_event: ft.ControlEvent) -> None:
        create_background_task(start_exploration())

    start_button = wv.build_start_button(on_click=on_start_click)
    loading_carousel, loading_emoji, loading_message = wv.build_loading_carousel()
    welcome_paper = cast(ft.Container, welcome_screen.content)
    welcome_content = cast(ft.Column, welcome_paper.content)
    welcome_content.controls.append(start_button)

    # Mode switching
    async def pause_camera_preview(camera_control: Any) -> None:
        try:
            await camera_control.pause_preview()
        except (AttributeError, RuntimeError):
            pass

    async def hide_camera_preview() -> None:
        state.camera_ready = False
        current_camera = state.camera
        state.camera = None
        camera.camera_preview_slot.visible = False
        camera.camera_preview_slot.content = camera.camera_placeholder
        if current_camera is not None:
            create_background_task(pause_camera_preview(current_camera))

    def restore_camera_preview() -> None:
        state.camera_ready = False
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
                on_click=lambda _event, next_value=value: create_background_task(switch_mode(next_value)),
            )
        return ft.Row(
            controls=[
                option("plant", MODE_ICONS[AppMode.PLANT], "\u690d\u7269"),
                option("animal", MODE_ICONS[AppMode.ANIMAL], "\u52d5\u7269"),
            ],
            spacing=24, alignment=ft.MainAxisAlignment.CENTER,
        )

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
        page.update()
        if value == "plant":
            create_background_task(camera.initialize())

    def toggle_dark_mode(_event: ft.ControlEvent | None = None) -> None:
        state.is_dark_mode = not state.is_dark_mode
        apply_theme(state.is_dark_mode)
        page.theme_mode = ft.ThemeMode.DARK if state.is_dark_mode else ft.ThemeMode.LIGHT
        page.bgcolor = THEME["PAGE_BG"]
        camera.apply_theme_colors()
        camera.render_handle(update_page=False)
        create_background_task(save_dark_mode_preference(state.is_dark_mode))
        _rebuild_visible_shell()
        page.update()

    # Shell rebuild
    def _rebuild_visible_shell() -> None:
        for ctrl in [gallery_service.grid, gallery_service.gallery_empty_state, mode, content_area]:
            if ctrl is not None and ctrl.parent is not None:
                try:
                    parent = cast(Any, ctrl.parent)
                    if hasattr(parent, "controls") and ctrl in parent.controls:
                        parent.controls.remove(ctrl)
                    elif hasattr(parent, "content") and parent.content == ctrl:
                        parent.content = None
                except (AttributeError, ValueError):
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
            new_content = av.get_animals_view(
                page,
                lambda name: dv.show_animal_card(page, state, status, gallery_service.add_animal, name),
            )
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
    mode: ft.Container = ft.Container(content=build_mode_selector())
    content_area: ft.Container = ft.Container(padding=4)

    shell: ft.Container = ft.Container(
        width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
        visible=False,
    )
    # Start exploration
    async def start_exploration() -> None:
        try:
            cast(Any, start_button).text = "\u6e96\u5099\u4e2d..."
            start_button.disabled = True
            await asyncio.sleep(0)

            async def build_shell() -> None:
                content_area.content = pv._build_plant_view(camera.magnifier_body, busy_ring, status,
                                                             restart_camera_button, organ_mode)
                camera.render_handle(update_page=False)
                if state.pokedex:
                    gallery_service.refresh(update_page=False)
                _rebuild_visible_shell()

            await build_shell()
            welcome_screen.visible = False
            shell.visible = True
            page.update()
            await page.scroll_to(offset=0)
            page.update()

            create_background_task(camera.initialize())
            report_performance(page)
        except Exception as error:
            page.clean()
            page.add(
                ft.Container(
                    width=min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2),
                    padding=24,
                    content=soft_card(
                        ft.Column(
                            controls=[
                                ft.Text("\u63a2\u96aa\u6d41\u7a0b\u555f\u52d5\u5931\u6557", size=24,
                                        weight=ft.FontWeight.W_900, color=THEME["TITLE"]),
                                ft.Text(str(error), size=13, color=THEME["BODY_DARK"], selectable=True),
                            ],
                            spacing=12,
                        )
                    ),
                )
            )
            page.update()

    page.add(welcome_screen, shell)
    await asyncio.sleep(0)
    mark_explorer_ready()

    def _on_page_resize(_event: ft.ControlEvent | None = None) -> None:
        w = min(CONTENT_MAX_WIDTH, (page.width or 480) - CONTENT_MIN_PADDING * 2)
        welcome_screen.width = w
        shell.width = w
        page.update()

    page.on_resize = _on_page_resize

    async def _on_page_close(_event: ft.ControlEvent | None = None) -> None:
        await flush_pokedex_save()

    page.on_close = _on_page_close


if os.environ.get("FLET_SKIP_RUN") != "1":
    ft.run(main)
