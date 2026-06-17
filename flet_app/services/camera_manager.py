from __future__ import annotations

import asyncio
from typing import Any

import flet as ft

try:
    import flet_camera as fc
except ImportError:
    fc = None

from app_state import AppState
from camera_utils import (
    CAMERA_ZOOM_STEP,
    LENS_FRAME_PADDING,
    LENS_FRAME_SIZE,
    LENS_VIEWPORT_SIZE,
    MAX_CAMERA_ZOOM,
    MIN_CAMERA_ZOOM,
    camera_preview_metrics,
    clamp_camera_zoom,
    select_preferred_cameras,
)
from config import (
    CAMERA_INITIALIZE_TIMEOUT,
    CAMERA_GET_AVAILABLE_TIMEOUT,
    MAX_CAMERA_INIT_ATTEMPTS,
)
from errors import CameraError
from magnifier_handle import MagnifierHandle
from plant_api import (
    PLANT_ORGAN_OPTIONS,
    RecognitionServiceError,
    card_image_from_capture_async,
    parse_plantnet_result,
    post_image_to_worker,
)
from ui_theme import THEME, border_all


def status_msg(text: str, level: str = "info") -> str:
    prefix = {"ok": "\u2705 ", "warn": "\u26a0\ufe0f ", "err": "\u274c ", "info": ""}
    return f"{prefix.get(level, '')}{text}"


def mark_load_timing(name: str) -> None:
    try:
        from js import performance  # type: ignore

        performance.mark(name)
    except (ImportError, AttributeError):
        pass


class CameraManager:
    def __init__(
        self,
        page: ft.Page,
        state: AppState,
        status_text: ft.Text,
        busy_ring: ft.ProgressRing,
        on_capture_result: Any = None,
        create_background_task: Any = None,
        get_selected_organ: Any = None,
        is_plant_mode: Any = None,
    ) -> None:
        from _types_reexport import VoidControlEventCallback, CreateBackgroundTask

        self._page = page
        self._state = state
        self._status_text = status_text
        self._busy_ring = busy_ring
        self._on_capture_result = on_capture_result  # type: ignore[assignment]
        self._create_background_task = create_background_task or (lambda _: None)  # type: ignore[arg-type]
        self._get_selected_organ = get_selected_organ or (lambda: "auto")
        self._is_plant_mode = is_plant_mode or (lambda: True)

        self.camera_placeholder = ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.EXPLORE, size=44, color=ft.Colors.WHITE70),
                    ft.Text("\u6b63\u5728\u6e96\u5099\u63a2\u96aa\u93e1\u982d", color=ft.Colors.WHITE70, weight=ft.FontWeight.W_700),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.camera_preview_slot = ft.Container(
            left=0, top=0,
            width=LENS_VIEWPORT_SIZE, height=LENS_VIEWPORT_SIZE,
            content=self.camera_placeholder,
        )
        self.camera_viewport = ft.Stack(
            width=LENS_VIEWPORT_SIZE, height=LENS_VIEWPORT_SIZE,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            controls=[self.camera_preview_slot],
        )

        self.camera_frame = ft.Container(
            width=LENS_FRAME_SIZE, height=LENS_FRAME_SIZE,
            border_radius=LENS_FRAME_SIZE / 2,
            bgcolor=THEME["CAMERA_BG"],
            padding=LENS_FRAME_PADDING,
            border=border_all(5, THEME["CAMERA_BORDER"]),
            shadow=ft.BoxShadow(blur_radius=34, color=THEME["SHADOW_CAMERA"], offset=ft.Offset(0, 14)),
            content=ft.Container(
                width=LENS_VIEWPORT_SIZE, height=LENS_VIEWPORT_SIZE,
                border_radius=LENS_VIEWPORT_SIZE / 2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor=THEME["CAMERA_INNER"],
                content=self.camera_viewport,
            ),
        )

        self.handle_slot = ft.Container(width=160, height=260)

        magnifier_handle_overlap = 24
        self.magnifier_body = ft.Stack(
            width=LENS_FRAME_SIZE,
            height=LENS_FRAME_SIZE + 260 - magnifier_handle_overlap,
            controls=[
                ft.Container(
                    left=(LENS_FRAME_SIZE - 120) / 2,
                    top=LENS_FRAME_SIZE - magnifier_handle_overlap,
                    width=160, height=260,
                    content=self.handle_slot,
                ),
                ft.Container(left=0, top=0, content=self.camera_frame),
            ],
        )

    def apply_theme_colors(self) -> None:
        self.camera_frame.bgcolor = THEME["CAMERA_BG"]
        self.camera_frame.border = border_all(5, THEME["CAMERA_BORDER"])
        self.camera_frame.shadow = ft.BoxShadow(
            blur_radius=34,
            color=THEME["SHADOW_CAMERA"],
            offset=ft.Offset(0, 14),
        )
        inner_frame = self.camera_frame.content
        if isinstance(inner_frame, ft.Container):
            inner_frame.bgcolor = THEME["CAMERA_INNER"]

    def apply_zoom(self, update_slot: bool = True) -> None:
        size, left, top = camera_preview_metrics(self._state.zoom_level)
        self.camera_preview_slot.left = left
        self.camera_preview_slot.top = top
        self.camera_preview_slot.width = size
        self.camera_preview_slot.height = size
        if self._state.camera is not None:
            self._state.camera.width = size
            self._state.camera.height = size
        if update_slot:
            self.camera_preview_slot.update()

    def adjust_zoom(self, delta: float) -> None:
        next_zoom = clamp_camera_zoom(self._state.zoom_level + delta)
        if next_zoom == self._state.zoom_level:
            return
        self._state.zoom_level = next_zoom
        self.apply_zoom()
        zoom_text = (
            f"\u653e\u5927 {self._state.zoom_level:.2g}x"
            if self._state.zoom_level > MIN_CAMERA_ZOOM
            else "\u56de\u5230\u539f\u59cb\u5927\u5c0f"
        )
        self._status_text.value = zoom_text
        self.render_handle(update_page=False)
        self._status_text.update()
        if self.handle_slot.page is not None:
            self.handle_slot.update()

    def render_handle(self, update_page: bool = True) -> None:
        self.handle_slot.content = MagnifierHandle(
            on_switch=self.switch_camera,
            on_capture=self.capture_and_identify,
            on_room_in=lambda _e: self.adjust_zoom(CAMERA_ZOOM_STEP),
            on_room_out=lambda _e: self.adjust_zoom(-CAMERA_ZOOM_STEP),
            switch_enabled=len(self._state.cameras) > 1,
            capture_enabled=self._state.camera_ready,
            room_in_enabled=self._state.zoom_level < MAX_CAMERA_ZOOM,
            room_out_enabled=self._state.zoom_level > MIN_CAMERA_ZOOM,
        )
        if update_page:
            self._page.update()

    async def switch_camera(self, _event: ft.ControlEvent | None = None) -> None:
        if self._state.camera is None:
            self._status_text.value = "\u6b64\u74b0\u5883\u5c1a\u672a\u8f09\u5165\u76f8\u6a5f\u5143\u4ef6"
            self._page.update()
            return
        if len(self._state.cameras) < 2:
            self._status_text.value = "\u6b64\u88dd\u7f6e\u6c92\u6709\u53ef\u5207\u63db\u7684\u7b2c\u4e8c\u93e1\u982d"
            self._page.update()
            return
        previous_index = self._state.selected_camera_index
        self._state.camera_ready = False
        self.render_handle()
        self._state.selected_camera_index = 1 if self._state.selected_camera_index == 0 else 0
        try:
            await self._state.camera.set_description(self._state.cameras[self._state.selected_camera_index])
            self._state.camera_ready = True
            self._status_text.value = (
                "\u5df2\u5207\u63db\u5230\u524d\u93e1\u982d"
                if self._state.selected_camera_index == 1
                else "\u5df2\u5207\u63db\u5230\u5f8c\u93e1\u982d"
            )
        except Exception as error:
            self._state.selected_camera_index = previous_index
            try:
                await self._state.camera.set_description(self._state.cameras[self._state.selected_camera_index])
            except (AttributeError, RuntimeError):
                pass
            self._state.camera_ready = True
            self._status_text.value = status_msg(
                f"\u93e1\u982d\u5207\u63db\u5931\u6557\uff0c\u5df2\u56de\u5230\u4e0a\u4e00\u9846\u93e1\u982d\uff1a{error}",
                "warn",
            )
        self.render_handle()
        self._page.update()

    async def capture_and_identify(self, _event: ft.ControlEvent | None = None) -> None:
        try:
            if self._state.camera is None or not self._state.camera_ready:
                if not self._state.camera_initializing:
                    self._status_text.value = "\u76f8\u6a5f\u5c1a\u672a\u5c31\u7e8c\uff0c\u6b63\u5728\u91cd\u65b0\u555f\u52d5..."
                    if self._create_background_task:
                        self._create_background_task(self.initialize())
                else:
                    self._status_text.value = "\u76f8\u6a5f\u6e96\u5099\u4e2d\uff0c\u8acb\u7a0d\u5019"
                self._page.update()
                return
            self._status_text.value = "\u6b63\u5728\u62cd\u651d\u4e26\u8fa8\u8b58..."
            self._busy_ring.visible = True
            self._page.update()
            mark_load_timing("art-village:identify-start")
            image_data = await self._state.camera.take_picture()
            try:
                selected_organ = self._get_selected_organ()
                payload = await post_image_to_worker(image_data, selected_organ)
                mark_load_timing("art-village:identify-primary-ready")
            except RecognitionServiceError as error:
                self._status_text.value = str(error)
                return
            except Exception as error:
                self._status_text.value = status_msg(
                    f"\u8fa8\u8b58\u66ab\u6642\u5931\u6557\uff0c\u8acb\u7a0d\u5f8c\u518d\u8a66\uff1a{error}",
                    "err",
                )
                return
            plant = parse_plantnet_result(payload)
            if plant is None:
                self._status_text.value = status_msg(
                    "找不到匹配的植物，請對準葉子、花或果實再拍一次",
                    "warn",
                )
                self._page.update()
                return
            plant["organ"] = selected_organ
            plant["organ_label"] = PLANT_ORGAN_OPTIONS.get(selected_organ, "自動")
            plant["captured_image"] = await card_image_from_capture_async(image_data)
            plant["worker_timing"] = payload.get("timing") or {}
            if self._on_capture_result:
                await self._on_capture_result(plant)
        except Exception as error:
            self._status_text.value = status_msg(f"\u8fa8\u8b58\u5931\u6557\uff1a{error}", "err")
        finally:
            self._busy_ring.visible = False
            self._page.update()

    async def initialize(self, _event: ft.ControlEvent | None = None) -> None:
        if not self._is_plant_mode():
            return
        if self._state.camera_initializing:
            self._status_text.value = "\u76f8\u6a5f\u6b63\u5728\u555f\u52d5\u4e2d\uff0c\u8acb\u7a0d\u5019"
            self._page.update()
            return
        self._state.camera_initializing = True
        try:
            mark_load_timing("art-village:camera-init-start")
            self._state.camera_ready = False
            self._status_text.value = (
                "\u6b63\u5728\u555f\u52d5\u76f8\u6a5f\uff0c\u82e5\u700f\u89bd\u5668\u554f\u554f\u6b0a\u9650\u8acb\u6309\u5141\u8a31..."
            )
            self.render_handle(update_page=False)
            if fc is None:
                self._status_text.value = "\u6b64\u700f\u89bd\u5668\u66ab\u6642\u7121\u6cd5\u8f09\u5165\u76f8\u6a5f\u5143\u4ef6"
                self.render_handle()
                self._page.update()
                return
            if self._state.camera is None:
                self._state.camera = fc.Camera(
                    width=self.camera_preview_slot.width,
                    height=self.camera_preview_slot.height,
                    preview_enabled=True,
                    content=ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=44, color=ft.Colors.WHITE70),
                    ),
                )
                self.apply_zoom(update_slot=False)
                self.camera_preview_slot.content = self._state.camera
                await asyncio.sleep(0)
            if not self._is_plant_mode():
                return
            self._status_text.value = "\u6b63\u5728\u5c0b\u627e\u53ef\u7528\u76f8\u6a5f..."
            self._page.update()
            last_error: Exception | None = None
            for attempt in range(MAX_CAMERA_INIT_ATTEMPTS):
                try:
                    self._state.cameras = await asyncio.wait_for(
                        self._state.camera.get_available_cameras(),
                        timeout=CAMERA_GET_AVAILABLE_TIMEOUT,
                    )
                    last_error = None
                    break
                except Exception as error:
                    last_error = error
                    error_text = str(error)
                    if (
                        "TimeoutException" not in error_text
                        and "TimeoutError" not in error_text
                    ) or attempt == MAX_CAMERA_INIT_ATTEMPTS - 1:
                        break
                    self._status_text.value = (
                        f"相機元件準備中，正在重試 {attempt + 2}/{MAX_CAMERA_INIT_ATTEMPTS}..."
                    )
                    self._page.update()
                    await asyncio.sleep(1.5)
            if last_error is not None:
                raise last_error
            if self._state.cameras:
                self._state.cameras = select_preferred_cameras(self._state.cameras)
                self._state.selected_camera_index = 0
                last_error = None
                for index, camera_description in enumerate(self._state.cameras):
                    self._state.selected_camera_index = index
                    self._status_text.value = f"\u6b63\u5728\u521d\u59cb\u5316\u76f8\u6a5f {index + 1}/{len(self._state.cameras)}..."
                    self._page.update()
                    if not self._is_plant_mode():
                        return
                    try:
                        await asyncio.wait_for(
                            self._state.camera.initialize(
                                camera_description,
                                fc.ResolutionPreset.MEDIUM,
                                enable_audio=False,
                            ),
                            timeout=CAMERA_INITIALIZE_TIMEOUT,
                        )
                        self._state.camera_ready = True
                        self._status_text.value = "\u76f8\u6a5f\u5df2\u555f\u52d5"
                        mark_load_timing("art-village:camera-ready")
                        break
                    except Exception as error:
                        last_error = error
                        self._state.camera_ready = False
                        await asyncio.sleep(0.4)
                if not self._state.camera_ready:
                    raise last_error or RuntimeError("\u6c92\u6709\u93e1\u982d\u53ef\u4ee5\u521d\u59cb\u5316")
            else:
                self._status_text.value = (
                "\u627e\u4e0d\u5230\u53ef\u7528\u76f8\u6a5f\uff0c\u8acb\u78ba\u8a8d\u700f\u89bd\u5668\u76f8\u6a5f\u6b0a\u9650\u5df2\u5141\u8a31"
            )
        except TimeoutError:
            self._state.camera_ready = False
            self._status_text.value = (
                "\u76f8\u6a5f\u555f\u52d5\u903e\u6642\uff0845\u79d2\uff09\uff0c\u8acb\u78ba\u8a8d\u700f\u89bd\u5668\u76f8\u6a5f\u6b0a\u9650\u5df2\u5141\u8a31\u4e26\u91cd\u65b0\u6574\u7406\u9801\u9762"
            )
        except Exception as error:
            self._state.camera_ready = False
            msg = (
                f"\u76f8\u6a5f\u555f\u52d5\u5931\u6557\uff1a{error}。"
                "請確認網址是 HTTPS 或 127.0.0.1，並允許相機權限。"
            )
            self._status_text.value = status_msg(msg, "err")
        finally:
            self._state.camera_initializing = False
        if self._is_plant_mode():
            self.render_handle()
        self._page.update()

    async def hide_preview(self) -> None:
        self._state.camera_ready = False
        if self._state.camera is not None:
            try:
                await self._state.camera.pause_preview()
            except (AttributeError, RuntimeError):
                pass
        self.camera_preview_slot.visible = False
        self.camera_preview_slot.content = self.camera_placeholder
        self._state.camera = None

    async def restore_preview(self) -> None:
        self.camera_preview_slot.visible = True
        self.camera_preview_slot.content = self.camera_placeholder
        await self.initialize()
