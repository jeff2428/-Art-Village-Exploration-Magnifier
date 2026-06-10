from __future__ import annotations

import json
from typing import Any

import flet as ft
from plant_api import (
    PLANT_ORGAN_OPTIONS,
    RecognitionServiceError,
    card_image_from_capture,
    get_metadata_from_worker,
    metadata_for_scientific_name,
    metadata_from_perenual,
    parse_plantnet_result,
    post_image_to_worker,
)
from pokedex_manager import save_cached_pokedex_debounced


def status_msg(text: str, level: str = "info") -> str:
    prefix = {"ok": "✅ ", "warn": "⚠️ ", "err": "❌ ", "info": ""}
    return f"{prefix.get(level, '')}{text}"


class RecognitionService:
    def __init__(
        self,
        page: ft.Page,
        state,
        status_text: ft.Text,
        create_background_task,
        mark_load_timing,
        initialize_camera=None,
        refresh_gallery=None,
    ):
        self.page = page
        self.state = state
        self.status_text = status_text
        self.create_background_task = create_background_task
        self.mark_load_timing = mark_load_timing
        self._initialize_camera = initialize_camera
        self._refresh_gallery = refresh_gallery

    async def capture_and_identify(
        self,
        camera,
        selected_organ_value,
        add_plant_to_gallery,
        show_plant_card,
        close_dialog,
        close_recognition_loading_card,
        show_recognition_loading_card,
    ):
        try:
            if camera is None or not self.state.camera_ready:
                if not self.state.camera_initializing:
                    self.status_text.value = "相機尚未就緒，正在重新啟動..."
                    if self._initialize_camera:
                        self.create_background_task(self._initialize_camera())
                else:
                    self.status_text.value = "相機準備中，請稍候"
                self.page.update()
                return
            self.status_text.value = "正在拍攝並辨識..."
            self.state.busy_ring.visible = True
            show_recognition_loading_card()
            self.page.update()
            self.mark_load_timing("art-village:identify-start")
            image_data = await camera.take_picture()
            try:
                selected_organ = selected_organ_value()
                payload = await post_image_to_worker(image_data, selected_organ)
                self.mark_load_timing("art-village:identify-primary-ready")
            except RecognitionServiceError as error:
                self.status_text.value = str(error)
                close_recognition_loading_card(update_page=False)
                return
            except Exception as error:
                self.status_text.value = status_msg(
                    f"辨識暫時失敗，請稍後再試：{error}", "err"
                )
                close_recognition_loading_card(update_page=False)
                return
            plant = parse_plantnet_result(payload)
            if plant is None:
                self.status_text.value = status_msg(
                    "找不到匹配的植物，請對準葉子、花或果實再拍一次", "warn"
                )
                close_recognition_loading_card(update_page=False)
                self.page.update()
                return
            plant["organ"] = selected_organ
            plant["organ_label"] = PLANT_ORGAN_OPTIONS.get(selected_organ, "自動")
            plant["captured_image"] = card_image_from_capture(image_data)
            plant["worker_timing"] = payload.get("timing") or {}
            add_plant_to_gallery(plant)
            close_recognition_loading_card(update_page=False)
            show_plant_card(plant["zh_name"], plant)
            plant_metadata_task = (
                self.refresh_plant_metadata(plant)
                if plant.get("metadata_status") == "pending"
                else None
            )
        except Exception as error:
            self.status_text.value = status_msg(f"辨識失敗：{error}", "err")
            close_recognition_loading_card(update_page=False)
            plant_metadata_task = None
        finally:
            self.state.busy_ring.visible = False
            self.page.update()
        if plant_metadata_task:
            self.create_background_task(plant_metadata_task)

    async def refresh_plant_metadata(self, plant: dict[str, Any]) -> None:
        scientific_name = plant.get("sci_name") or ""
        if not scientific_name or plant.get("metadata_status") not in ("pending", "error"):
            return
        try:
            metadata_payload = await get_metadata_from_worker(scientific_name)
            if metadata_payload.get("status") not in ("ok", "cached"):
                plant["metadata_status"] = metadata_payload.get("status", "error")
                self.state.pokedex[plant["zh_name"]] = plant
                await save_cached_pokedex_debounced(self.state.pokedex)
                return
            fallback = metadata_for_scientific_name(scientific_name)
            enriched_metadata = metadata_from_perenual(metadata_payload, fallback)
            plant["toxicity"] = enriched_metadata["toxicity"]
            plant["invasive"] = enriched_metadata["invasive"]
            plant["care"] = enriched_metadata["care"]
            plant["metadata_source"] = enriched_metadata["source"]
            plant["metadata_status"] = metadata_payload.get("status", "ok")
            if metadata_payload.get("description"):
                plant["desc"] = metadata_payload["description"]
            self.state.pokedex[plant["zh_name"]] = plant
            self.status_text.value = f"{plant['zh_name']} 的 Perenual 資料已補上"
            if self._refresh_gallery:
                self._refresh_gallery(update_page=False)
            self.page.update()
        except (OSError, json.JSONDecodeError, KeyError, AttributeError):
            plant["metadata_status"] = "error"
            self.state.pokedex[plant["zh_name"]] = plant
            await save_cached_pokedex_debounced(self.state.pokedex)
