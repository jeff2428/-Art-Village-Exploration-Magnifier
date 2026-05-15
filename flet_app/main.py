from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any

import flet as ft

try:
    import flet_camera as fc
except Exception:
    fc = None  # type: ignore[assignment]

from magnifier_handle import MagnifierHandle

try:
    from build_config import WORKER_URL
except ImportError:
    WORKER_URL = "https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev"

POKEDEX_STORAGE_KEY = "artVillagePokedex"
LOCAL_CACHE_DIR = Path(tempfile.gettempdir()) / "art-village-exploration-magnifier"
LOCAL_CACHE_PATH = LOCAL_CACHE_DIR / "local_pokedex_cache.json"
LOW_CONFIDENCE_THRESHOLD = 70.0
LENS_VIEWPORT_SIZE = 304
LENS_FRAME_SIZE = 336
LENS_FRAME_PADDING = 11
CAMERA_PREVIEW_SIZE = 420
CAMERA_PREVIEW_OFFSET = -58

ANIMALS_DB = {
    "貝貝": {
        "type": "animal",
        "emoji": "🐶",
        "role": "溫柔導覽員",
        "desc": "東北角的米克斯母狗，也是藝素村最溫柔的導嚮員。",
    },
    "牧耳": {
        "type": "animal",
        "emoji": "🐕",
        "role": "草地巡邏員",
        "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。",
    },
    "小飛俠": {
        "type": "animal",
        "emoji": "🐈",
        "role": "屋頂觀察員",
        "desc": "身手矯健，總是在屋頂上觀察探險家們。",
    },
    "嘿皮": {
        "type": "animal",
        "emoji": "🐈‍⬛",
        "role": "親人接待員",
        "desc": "個性大方的黑貓，討摸是牠的日常。",
    },
    "冬瓜": {
        "type": "animal",
        "emoji": "🐱",
        "role": "慵懶守護者",
        "desc": "圓滾滾的橘貓，是村裡的慵懶大王。",
    },
}


def border_all(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
    return ft.Container(
        bgcolor="#fffdf4",
        border_radius=16,
        padding=padding,
        border=border_all(1, "#dccfc0"),
        shadow=ft.BoxShadow(blur_radius=16, color="#2b130814", offset=ft.Offset(0, 8)),
        content=content,
    )


def section_label(icon: str, text: str) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Text(icon, size=24),
            ft.Text(text, size=24, weight=ft.FontWeight.W_900, color="#3d2a21"),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def first_common_name(species: dict[str, Any], chinese: bool) -> str | None:
    for name in species.get("commonNames", []) or []:
        has_cjk = any("\u4e00" <= char <= "\u9fff" for char in name)
        if chinese == has_cjk:
            return name
    return None


def plant_candidate_from_result(result: dict[str, Any]) -> dict[str, Any]:
    species = result.get("species") or {}
    scientific = species.get("scientificNameWithoutAuthor") or species.get("scientificName") or "Unknown"
    zh_name = first_common_name(species, chinese=True) or scientific
    eng_name = first_common_name(species, chinese=False) or "N/A"
    score = float(result.get("score") or 0)
    confidence = round(score * 100, 1)

    return {
        "zh_name": zh_name,
        "eng_name": eng_name,
        "sci_name": scientific,
        "emoji": "🌿",
        "type": "plant",
        "desc": f"PlantNet 推測為 {zh_name}（{scientific}）。",
        "confidence": confidence,
        "is_low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
    }


def parse_plantnet_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    results = payload.get("results") or []
    if not results:
        return None

    candidates = [plant_candidate_from_result(result or {}) for result in results[:4]]
    primary = candidates[0]
    primary["alternatives"] = candidates[1:]
    primary["needs_confirmation"] = primary["is_low_confidence"]
    return primary


def confidence_text(item: dict[str, Any]) -> str:
    confidence = item.get("confidence", 0)
    if not confidence:
        return ""
    suffix = "，建議確認" if item.get("is_low_confidence") else ""
    return f"信心度 {confidence}%{suffix}"


def capture_to_bytes(capture: Any) -> tuple[bytes, str]:
    if isinstance(capture, bytes):
        return capture, "image/jpeg"
    if isinstance(capture, bytearray):
        return bytes(capture), "image/jpeg"
    if isinstance(capture, memoryview):
        return capture.tobytes(), "image/jpeg"

    if isinstance(capture, str) and capture.startswith("data:"):
        header, encoded = capture.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
        return base64.b64decode(encoded), mime

    if isinstance(capture, str):
        image_path = Path(capture)
        if image_path.exists():
            mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
            return image_path.read_bytes(), mime
        return base64.b64decode(capture), "image/jpeg"

    raise TypeError("相機回傳了無法辨識的圖片格式")


class RecognitionServiceError(RuntimeError):
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def post_image_to_worker_sync(binary: bytes, mime: str) -> dict[str, Any]:
    import requests

    response = requests.post(
        WORKER_URL,
        files={"images": ("capture.jpg", binary, mime)},
        timeout=30,
    )
    if not response.ok:
        raise RecognitionServiceError(worker_error_message(response.status_code, response.text))
    return response.json()


def worker_error_message(status_code: int, text: str) -> str:
    snippet = " ".join((text or "").strip().split())[:120]
    if status_code == 404 and "1042" in snippet:
        return "辨識服務尚未部署，請檢查 Worker 網址"
    if status_code in (400, 404):
        return "沒有辨識到植物，請對準葉子、花或果實再拍一次"
    if status_code == 405:
        return "辨識服務方法錯誤，請重新整理頁面後再試"
    if status_code in (401, 403):
        return "辨識服務金鑰未通過，請檢查 Worker 的 PLANTNET_API_KEY"
    if status_code == 413:
        return "照片太大，請靠近植物後再拍一次"
    if status_code == 426:
        return "前端版本過舊，請重新整理頁面後再拍一次"
    if status_code == 429:
        return "辨識服務忙碌，請稍後再試"
    if 500 <= status_code < 600:
        return "辨識服務暫時忙碌，請稍後再試"
    return f"辨識服務暫時無法處理（{status_code}）"


async def post_image_to_worker(capture: Any) -> dict[str, Any]:
    if "YOUR-WORKER" in WORKER_URL:
        raise RuntimeError("尚未設定 Cloudflare Pages 的 WORKER_URL")

    binary, mime = capture_to_bytes(capture)

    try:
        from js import Blob, FormData, Object, Uint8Array, fetch  # type: ignore
        from pyodide.ffi import to_js  # type: ignore

        image_array = Uint8Array.new(to_js(list(binary)))
        blob = Blob.new([image_array], {"type": mime})

        form = FormData.new()
        form.append("images", blob, "capture.jpg")

        fetch_options = to_js({"method": "POST", "body": form}, dict_converter=Object.fromEntries)
        response = await fetch(WORKER_URL, fetch_options)
        text = await response.text()
        if not response.ok:
            raise RecognitionServiceError(worker_error_message(response.status, text))
        return json.loads(text)
    except ModuleNotFoundError:
        return await asyncio.to_thread(post_image_to_worker_sync, binary, mime)


def load_json_cache(storage_key: str, local_path: Path, fallback: Any) -> Any:
    try:
        from js import localStorage  # type: ignore

        raw = localStorage.getItem(storage_key)
        if raw:
            cached = json.loads(raw)
            return cached
    except Exception:
        pass

    try:
        if not local_path.exists():
            return fallback
        try:
            return json.loads(local_path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    except Exception:
        return fallback


def save_json_cache(storage_key: str, local_path: Path, data: Any) -> None:
    serialized = json.dumps(data, ensure_ascii=False)
    try:
        from js import localStorage  # type: ignore

        localStorage.setItem(storage_key, serialized)
        return
    except Exception:
        pass

    try:
        if data in ({}, []):
            return
        if local_path.exists() and local_path.read_text(encoding="utf-8") == serialized:
            return
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(serialized, encoding="utf-8")
    except Exception:
        return


def load_cached_pokedex() -> dict[str, dict[str, Any]]:
    cached = load_json_cache(POKEDEX_STORAGE_KEY, LOCAL_CACHE_PATH, {})
    return cached if isinstance(cached, dict) else {}


def save_cached_pokedex(pokedex: dict[str, dict[str, Any]]) -> None:
    save_json_cache(POKEDEX_STORAGE_KEY, LOCAL_CACHE_PATH, pokedex)


def clear_legacy_snapshot_cache() -> None:
    try:
        from js import localStorage  # type: ignore

        localStorage.removeItem("artVillageSnapshotQueue")
    except Exception:
        pass

    try:
        legacy_path = LOCAL_CACHE_DIR / "local_snapshot_queue.json"
        if legacy_path.exists():
            legacy_path.unlink()
    except Exception:
        pass


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


async def main(page: ft.Page) -> None:
    try:
        await run_app(page)
    except Exception as error:
        page.clean()
        page.bgcolor = "#f3efd9"
        page.add(
            ft.Container(
                padding=24,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    [
                        ft.Text("探險放大鏡載入失敗", size=26, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.Text(str(error), size=14, color="#5c4032", selectable=True),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        page.update()


async def run_app(page: ft.Page) -> None:
    page.title = "藝素村探險放大鏡"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor = "#f3efd9"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(
        ft.Container(
            padding=16,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(
                "探險放大鏡啟動中...",
                size=22,
                weight=ft.FontWeight.W_900,
                color="#3d2a21",
            ),
        )
    )
    page.update()

    pokedex: dict[str, dict[str, Any]] = load_cached_pokedex()
    clear_legacy_snapshot_cache()
    cameras: list[Any] = []
    selected_camera_index = 0
    camera_ready = False

    status = ft.Text(
        "",
        size=13,
        color="#6d5140",
        weight=ft.FontWeight.W_800,
        text_align=ft.TextAlign.CENTER,
        expand=True,
    )
    busy_ring = ft.ProgressRing(width=22, height=22, stroke_width=3, visible=False, color="#8a5a22")
    grid = ft.GridView(
        expand=False,
        max_extent=180,
        child_aspect_ratio=2.8,
        spacing=10,
        run_spacing=10,
        height=260,
    )

    camera = None
    camera_placeholder = ft.Container(
        alignment=ft.Alignment(0, 0),
        padding=20,
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.EXPLORE, size=44, color=ft.Colors.WHITE70),
                ft.Text("正在準備探險鏡頭", color=ft.Colors.WHITE70, weight=ft.FontWeight.W_700),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    camera_viewport = ft.Stack(
        width=LENS_VIEWPORT_SIZE,
        height=LENS_VIEWPORT_SIZE,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        controls=[
            ft.Container(
                left=0,
                top=0,
                width=LENS_VIEWPORT_SIZE,
                height=LENS_VIEWPORT_SIZE,
                content=camera_placeholder,
            )
        ],
    )
    camera_frame = ft.Container(
        width=LENS_FRAME_SIZE,
        height=LENS_FRAME_SIZE,
        border_radius=LENS_FRAME_SIZE / 2,
        bgcolor="#4d3026",
        padding=LENS_FRAME_PADDING,
        border=border_all(5, "#2b160f"),
        shadow=ft.BoxShadow(blur_radius=34, color="#442f2529", offset=ft.Offset(0, 14)),
        content=ft.Container(
            width=LENS_VIEWPORT_SIZE,
            height=LENS_VIEWPORT_SIZE,
            border_radius=LENS_VIEWPORT_SIZE / 2,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#0f1512",
            content=camera_viewport,
        ),
    )

    handle_slot = ft.Container(width=120, height=260)
    magnifier_handle_overlap = 24
    magnifier_body = ft.Stack(
        width=LENS_FRAME_SIZE,
        height=LENS_FRAME_SIZE + 260 - magnifier_handle_overlap,
        controls=[
            ft.Container(
                left=(LENS_FRAME_SIZE - 120) / 2,
                top=LENS_FRAME_SIZE - magnifier_handle_overlap,
                width=120,
                height=260,
                content=handle_slot,
            ),
            ft.Container(left=0, top=0, content=camera_frame),
        ],
    )
    content_area = ft.Container(width=380)

    def refresh_gallery(update_page: bool = True) -> None:
        grid.controls.clear()
        for name, item in pokedex.items():
            icon = item.get("emoji", "🌿" if item.get("type") == "plant" else "🐾")
            is_low_confidence = item.get("is_low_confidence", False)
            badge = "⚠️" if is_low_confidence else ""
            subtitle = confidence_text(item) or item.get("role", "")

            grid.controls.append(
                ft.Container(
                    bgcolor="#fffdf4",
                    border_radius=12,
                    padding=12,
                    alignment=ft.Alignment(0, 0),
                    border=border_all(1, "#d7c8b9"),
                    shadow=ft.BoxShadow(blur_radius=10, color="#2b130810", offset=ft.Offset(0, 5)),
                    animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                    tooltip=f"{name} 詳細介紹",
                    on_click=lambda _event, item_name=name, item_data=item: show_gallery_card(item_name, item_data),
                    on_long_press=lambda _event, item_name=name: confirm_delete_gallery_item(item_name),
                    content=ft.Column(
                        controls=[
                            ft.Text(f"{icon} {badge} {name}", size=14, weight=ft.FontWeight.W_800, color="#3d2a21"),
                            ft.Text(subtitle, size=11, color="#6d5140"),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        save_cached_pokedex(pokedex)
        if update_page:
            page.update()

    def add_animal_to_gallery(name: str) -> None:
        data = ANIMALS_DB[name]
        pokedex[name] = {"zh_name": name, **data}
        status.value = f"已遇見：{name}"
        refresh_gallery()

    def add_plant_to_gallery(plant: dict[str, Any]) -> None:
        pokedex[plant["zh_name"]] = plant
        if plant.get("is_low_confidence", False):
            status.value = f"⚠️ {plant['zh_name']}（信心度低，建議確認）"
        else:
            status.value = f"辨識成功：{plant['zh_name']} · {plant.get('confidence', 0)}%"
        refresh_gallery()

    def close_dialog(_event: ft.ControlEvent) -> None:
        page.pop_dialog()
        page.update()

    def delete_gallery_item(name: str) -> None:
        if name in pokedex:
            pokedex.pop(name)
            save_cached_pokedex(pokedex)
            status.value = f"已刪除：{name}"
            refresh_gallery()
        page.pop_dialog()
        page.update()

    def clear_gallery() -> None:
        pokedex.clear()
        save_cached_pokedex(pokedex)
        status.value = "已清除探險圖鑑"
        refresh_gallery()
        page.pop_dialog()
        page.update()

    def confirm_delete_gallery_item(name: str) -> None:
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("刪除圖鑑卡片", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text(f"要從探險圖鑑刪除「{name}」嗎？", size=15, color="#3d2a21"),
                actions=[
                    ft.TextButton("取消", on_click=close_dialog),
                    ft.TextButton("刪除", icon=ft.Icons.DELETE_OUTLINE, on_click=lambda _event: delete_gallery_item(name)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def confirm_clear_gallery(_event: ft.ControlEvent) -> None:
        if not pokedex:
            status.value = "探險圖鑑目前是空的"
            page.update()
            return
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("清除探險圖鑑", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text("要刪除所有圖鑑卡片嗎？這個動作無法復原。", size=15, color="#3d2a21"),
                actions=[
                    ft.TextButton("取消", on_click=close_dialog),
                    ft.TextButton("全部清除", icon=ft.Icons.DELETE_SWEEP_OUTLINED, on_click=lambda _event: clear_gallery()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def show_animal_card(name: str) -> None:
        data = ANIMALS_DB[name]
        add_animal_to_gallery(name)
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"{data['emoji']} {name}", size=24, weight=ft.FontWeight.W_900),
                content=soft_card(
                    ft.Column(
                        controls=[
                            ft.Text(data["role"], size=14, color="#7a4b38", weight=ft.FontWeight.W_800),
                            ft.Text(data["desc"], size=15, color="#3d2a21"),
                            ft.Text("已加入探險圖鑑", size=13, color="#2f7d51", weight=ft.FontWeight.W_800),
                        ],
                        spacing=8,
                    ),
                    padding=18,
                ),
                actions=[ft.TextButton("關閉", on_click=close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def show_gallery_card(name: str, data: dict[str, Any]) -> None:
        if data.get("type") == "animal":
            show_animal_card(name)
        else:
            show_plant_card(name, data)

    def show_plant_card(name: str, data: dict[str, Any]) -> None:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        alternatives = data.get("alternatives") or []
        
        warning_text: ft.Control = ft.Container()
        if is_low_confidence and confidence > 0:
            warning_text = ft.Container(
                padding=8,
                margin=ft.Margin.only(bottom=8),
                bgcolor="#fff3cd",
                border_radius=8,
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_OUTLINED, size=16, color="#856404"),
                        ft.Text(f"置信度僅 {confidence}%，建議實地確認物種", size=13, color="#856404", weight=ft.FontWeight.W_700),
                    ],
                    spacing=6,
                ),
            )

        alternative_controls: list[ft.Control] = []
        if alternatives:
            alternative_controls = [
                ft.Text("備選辨識", size=14, color="#3d2a21", weight=ft.FontWeight.W_900),
                *[
                    ft.Container(
                        padding=8,
                        border_radius=10,
                        bgcolor="#f7f0df",
                        content=ft.Text(
                            f"{candidate['zh_name']} · {candidate['confidence']}%",
                            size=12,
                            color="#5c4032",
                        ),
                    )
                    for candidate in alternatives
                ],
            ]
        
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"{data['emoji']} {name}", size=24, weight=ft.FontWeight.W_900),
                content=soft_card(
                    ft.Column(
                        controls=[
                            warning_text,
                            ft.Text(data["desc"], size=15, color="#3d2a21"),
                            ft.Text(confidence_text(data), size=13, color="#6d5140"),
                            *alternative_controls,
                            ft.Text("已加入探險圖鑑", size=13, color="#2f7d51", weight=ft.FontWeight.W_800),
                        ],
                        spacing=8,
                    ),
                    padding=18,
                ),
                actions=[ft.TextButton("關閉", on_click=close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    async def switch_camera(_event: ft.ControlEvent) -> None:
        nonlocal selected_camera_index, camera_ready
        if camera is None:
            status.value = "此環境尚未載入相機元件"
            page.update()
            return
        if len(cameras) < 2:
            status.value = "此裝置沒有可切換的第二鏡頭"
            page.update()
            return
        camera_ready = False
        render_handle()
        selected_camera_index = (selected_camera_index + 1) % len(cameras)
        await camera.set_description(cameras[selected_camera_index])
        camera_ready = True
        render_handle()
        status.value = "已切換鏡頭"
        page.update()

    async def capture_and_identify(_event: ft.ControlEvent) -> None:
        try:
            if camera is None or not camera_ready:
                status.value = "相機準備中，請稍候"
                page.update()
                return
            status.value = "正在拍攝並辨識..."
            busy_ring.visible = True
            page.update()
            image_data = await camera.take_picture()
            try:
                payload = await post_image_to_worker(image_data)
            except RecognitionServiceError as error:
                status.value = str(error)
                return
            except Exception as error:
                status.value = f"辨識暫時失敗，請稍後再試：{error}"
                return
            plant = parse_plantnet_result(payload)
            if plant is None:
                status.value = "找不到匹配的植物"
                page.update()
                return
            add_plant_to_gallery(plant)
        except Exception as error:
            status.value = f"辨識失敗：{error}"
        finally:
            busy_ring.visible = False
            page.update()

    def render_handle(update_page: bool = True) -> None:
        handle_slot.content = MagnifierHandle(
            on_switch=switch_camera,
            on_capture=capture_and_identify,
            switch_enabled=len(cameras) > 1,
            capture_enabled=camera_ready,
        )
        if update_page:
            page.update()

    async def initialize_camera(_event: ft.ControlEvent | None = None) -> None:
        nonlocal cameras, camera, camera_ready
        try:
            mark_load_timing("art-village:camera-init-start")
            camera_ready = False
            status.value = "正在啟動相機..."
            render_handle(update_page=False)
            page.update()
            if fc is None:
                status.value = "此瀏覽器暫時無法載入相機元件"
                render_handle()
                return
            if camera is None:
                camera = fc.Camera(
                    width=CAMERA_PREVIEW_SIZE,
                    height=CAMERA_PREVIEW_SIZE,
                    preview_enabled=True,
                    content=ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=44, color=ft.Colors.WHITE70),
                    ),
                )
                camera_viewport.controls = [
                    ft.Container(
                        left=CAMERA_PREVIEW_OFFSET,
                        top=CAMERA_PREVIEW_OFFSET,
                        width=CAMERA_PREVIEW_SIZE,
                        height=CAMERA_PREVIEW_SIZE,
                        content=camera,
                    )
                ]
                page.update()
                await asyncio.sleep(0)
            status.value = "正在尋找可用相機..."
            page.update()
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    cameras = await camera.get_available_cameras()
                    last_error = None
                    break
                except Exception as error:
                    last_error = error
                    if "TimeoutException" not in str(error) or attempt == 2:
                        break
                    status.value = f"相機元件準備中，正在重試 {attempt + 2}/3..."
                    page.update()
                    await asyncio.sleep(1.5)
            if last_error is not None:
                raise last_error
            if cameras:
                status.value = "正在初始化相機..."
                page.update()
                await camera.initialize(cameras[0], fc.ResolutionPreset.MEDIUM, enable_audio=False)
                camera_ready = True
                status.value = "相機已啟動"
                mark_load_timing("art-village:camera-ready")
            else:
                status.value = "找不到可用相機"
        except Exception as error:
            camera_ready = False
            status.value = f"相機啟動失敗：{error}"
        render_handle()

    background_tasks: set[asyncio.Task[Any]] = set()

    def create_background_task(coro: Any) -> None:
        task = asyncio.create_task(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    async def hydrate_gallery() -> None:
        await asyncio.sleep(0)
        refresh_gallery()

    mode = ft.RadioGroup(
        value="plant",
        content=ft.Row(
            controls=[
                ft.Radio(value="plant", label="🌿 尋找植物"),
                ft.Radio(value="animal", label="🐾 認識動物"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    def plant_card(name: str, data: dict[str, Any]) -> ft.Container:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        
        badge = ""
        if is_low_confidence and confidence > 0:
            badge = "⚠️"
        
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, plant_name=name: show_plant_card(plant_name, data),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{data['emoji']} {badge}", size=34),
                            ft.Column(
                                controls=[
                                    ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                                    ft.Text(f"置信度: {confidence}%" if confidence > 0 else "", size=13, weight=ft.FontWeight.W_700, color="#6d5140"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def animal_card(name: str, data: dict[str, str]) -> ft.Container:
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, pet=name: show_animal_card(pet),
            content=ft.Row(
                controls=[
                    ft.Text(data["emoji"], size=34),
                    ft.Column(
                        controls=[
                            ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                            ft.Text(data["role"], size=13, weight=ft.FontWeight.W_700, color="#7a4b38"),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    animals_view: ft.Column | None = None

    def get_animals_view() -> ft.Column:
        nonlocal animals_view
        if animals_view is None:
            animals_view = ft.Column(
                controls=[
                    section_label("🐾", "認識動物"),
                    ft.Text("點擊名字，打開牠的介紹卡片。", size=14, color="#6d5140"),
                    ft.Column(
                        controls=[animal_card(name, data) for name, data in ANIMALS_DB.items()],
                        spacing=12,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return animals_view

    plant_view = ft.Column(
        controls=[
            magnifier_body,
            ft.Row(
                controls=[busy_ring, status],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def update_mode(_event: ft.ControlEvent | None = None) -> None:
        if mode.value == "animal":
            content_area.content = get_animals_view()
        else:
            content_area.content = plant_view
        page.update()

    mode.on_change = update_mode

    def plant_card(name: str, data: dict[str, Any]) -> ft.Container:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        
        badge = ""
        if is_low_confidence and confidence > 0:
            badge = "⚠️"
        
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, plant_name=name: show_plant_card(plant_name, data),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{data['emoji']} {badge}", size=34),
                            ft.Column(
                                controls=[
                                    ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                                    ft.Text(f"置信度: {confidence}%" if confidence > 0 else "", size=13, weight=ft.FontWeight.W_700, color="#6d5140"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    gallery_panel = soft_card(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("🎒", size=30),
                        ft.Text("探險圖鑑", size=28, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            icon_color="#8a5a22",
                            tooltip="清除圖鑑內容",
                            on_click=confirm_clear_gallery,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                grid,
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
    )

    shell = ft.Container(
        width=430,
        padding=18,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("探險放大鏡", size=36, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.Text("🔍", size=34),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                soft_card(mode, padding=10),
                content_area,
                gallery_panel,
            ],
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    page.clean()
    page.add(shell)
    content_area.content = plant_view
    render_handle(update_page=False)
    page.update()
    mark_load_timing("art-village:flet-shell-ready")
    mark_explorer_ready()
    create_background_task(hydrate_gallery())
    create_background_task(initialize_camera())


if os.environ.get("FLET_SKIP_RUN") != "1":
    ft.run(main)
