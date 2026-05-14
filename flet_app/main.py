from __future__ import annotations

import json
from typing import Any

import flet as ft
import flet_camera as fc

from magnifier_handle import MagnifierHandle

try:
    from build_config import WORKER_URL
except ImportError:
    WORKER_URL = "https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev"

ANIMALS_DB = {
    "貝貝": {"type": "animal", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗，也是藝素村最溫柔的導嚮員。"},
    "牧耳": {"type": "animal", "emoji": "🐕", "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。"},
    "小飛俠": {"type": "animal", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察探險家們。"},
    "嘿皮": {"type": "animal", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，討摸是牠的日常。"},
    "冬瓜": {"type": "animal", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"},
}


def first_common_name(species: dict[str, Any], chinese: bool) -> str | None:
    for name in species.get("commonNames", []) or []:
        has_cjk = any("\u4e00" <= char <= "\u9fff" for char in name)
        if chinese == has_cjk:
            return name
    return None


def parse_plantnet_result(payload: dict[str, Any]) -> dict[str, str] | None:
    results = payload.get("results") or []
    if not results:
        return None

    species = (results[0] or {}).get("species") or {}
    scientific = species.get("scientificNameWithoutAuthor") or species.get("scientificName") or "Unknown"
    zh_name = first_common_name(species, chinese=True) or scientific
    eng_name = first_common_name(species, chinese=False) or "N/A"

    return {
        "zh_name": zh_name,
        "eng_name": eng_name,
        "sci_name": scientific,
        "emoji": "🌿",
        "type": "plant",
        "desc": f"PlantNet 推測為 {zh_name}（{scientific}）。",
    }


async def post_image_to_worker(data_url: str) -> dict[str, Any]:
    # Flet Web runs on Pyodide, so use the browser Fetch/FormData APIs directly.
    from js import Blob, FormData, Uint8Array, fetch  # type: ignore
    from pyodide.ffi import to_js  # type: ignore

    header, encoded = data_url.split(",", 1)
    mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
    binary = __import__("base64").b64decode(encoded)
    image_array = Uint8Array.new(to_js(list(binary)))
    blob = Blob.new([image_array], {"type": mime})

    form = FormData.new()
    form.append("images", blob, "capture.jpg")

    response = await fetch(WORKER_URL, {"method": "POST", "body": form})
    text = await response.text()
    if not response.ok:
        raise RuntimeError(f"辨識服務回應失敗：{response.status}")
    return json.loads(text)


async def main(page: ft.Page) -> None:
    page.title = "藝素村探險放大鏡"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor = "#edf4dc"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    pokedex: dict[str, dict[str, str]] = {}
    cameras: list[fc.CameraDescription] = []
    selected_camera_index = 0

    status = ft.Text("準備探索", size=14, color="#3d2a21", weight=ft.FontWeight.W_700)
    grid = ft.GridView(
        expand=False,
        max_extent=180,
        child_aspect_ratio=2.8,
        spacing=10,
        run_spacing=10,
        height=260,
    )

    camera = fc.Camera(
        expand=True,
        preview_enabled=True,
        content=ft.Container(
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=44, color=ft.Colors.WHITE70),
        ),
    )
    camera_frame = ft.Container(
        width=320,
        height=320,
        border_radius=160,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        bgcolor="#0f1512",
        border=ft.border.all(12, "#fff8df"),
        shadow=ft.BoxShadow(blur_radius=28, color="#442f2519", offset=ft.Offset(0, 12)),
        content=camera,
    )

    handle_slot = ft.Container()

    def refresh_gallery() -> None:
        grid.controls.clear()
        for name, item in pokedex.items():
            icon = item.get("emoji", "🌿" if item.get("type") == "plant" else "🐾")
            grid.controls.append(
                ft.Container(
                    bgcolor="#fffdf4",
                    border_radius=12,
                    padding=12,
                    alignment=ft.alignment.center,
                    border=ft.border.all(1, "#d7c8b9"),
                    content=ft.Text(f"{icon} {name}", size=16, weight=ft.FontWeight.W_800, color="#3d2a21"),
                )
            )
        page.update()

    async def switch_camera(_event: ft.ControlEvent) -> None:
        nonlocal selected_camera_index
        if len(cameras) < 2:
            status.value = "此裝置沒有可切換的第二鏡頭"
            page.update()
            return
        selected_camera_index = (selected_camera_index + 1) % len(cameras)
        await camera.set_description(cameras[selected_camera_index])
        status.value = "已切換鏡頭"
        page.update()

    async def capture_and_identify(_event: ft.ControlEvent) -> None:
        status.value = "正在拍攝並辨識..."
        page.update()
        try:
            image_data = await camera.take_picture()
            payload = await post_image_to_worker(image_data)
            plant = parse_plantnet_result(payload)
            if plant is None:
                status.value = "找不到匹配的植物"
                page.update()
                return
            pokedex[plant["zh_name"]] = plant
            status.value = f"辨識成功：{plant['zh_name']}"
            refresh_gallery()
        except Exception as error:
            status.value = f"辨識失敗：{error}"
            page.update()

    def render_handle() -> None:
        handle_slot.content = MagnifierHandle(
            on_switch=switch_camera,
            on_capture=capture_and_identify,
            switch_enabled=len(cameras) > 1,
        )
        page.update()

    async def initialize_camera(_event: ft.ControlEvent | None = None) -> None:
        nonlocal cameras
        cameras = await camera.get_available_cameras()
        if cameras:
            await camera.initialize(cameras[0], fc.ResolutionPreset.MEDIUM, enable_audio=False)
            status.value = "相機已啟動"
        else:
            status.value = "找不到可用相機"
        render_handle()

    mode = ft.SegmentedButton(
        selected={"plant"},
        segments=[
            ft.Segment(value="plant", label=ft.Text("🌿 尋找植物")),
            ft.Segment(value="animal", label=ft.Text("🐾 認識動物")),
        ],
    )

    animal_buttons = ft.Row(
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.FilledTonalButton(
                text=f"{data['emoji']} {name}",
                on_click=lambda _event, pet=name: (
                    pokedex.update({pet: {"zh_name": pet, **ANIMALS_DB[pet]}}),
                    refresh_gallery(),
                ),
            )
            for name, data in ANIMALS_DB.items()
        ],
    )

    page.add(
        ft.SafeArea(
            ft.Column(
                [
                    ft.Text("探險放大鏡 🔍", size=36, weight=ft.FontWeight.W_900, color="#3d2a21"),
                    mode,
                    camera_frame,
                    ft.Container(height=238, content=handle_slot),
                    status,
                    ft.Text("🎒 探險圖鑑", size=28, weight=ft.FontWeight.W_900, color="#3d2a21"),
                    animal_buttons,
                    grid,
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
    )
    page.on_connect = initialize_camera


ft.app(main)
