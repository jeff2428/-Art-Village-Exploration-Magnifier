from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import flet as ft
from app_state import AppState
from config import MAX_METADATA_RETRIES
from plant_api import (
    get_metadata_from_worker,
    metadata_for_scientific_name,
    metadata_from_perenual,
)
from pokedex_manager import save_cached_pokedex_debounced


class RecognitionService:
    def __init__(
        self,
        page: ft.Page,
        state: AppState,
        status_text: ft.Text,
        create_background_task: Callable,
        refresh_gallery: Callable | None = None,
    ):
        self.page = page
        self.state = state
        self.status_text = status_text
        self.create_background_task = create_background_task
        self._refresh_gallery = refresh_gallery

    async def refresh_plant_metadata(self, plant: dict[str, Any]) -> None:
        scientific_name = plant.get("sci_name") or ""
        metadata_status = plant.get("metadata_status")
        metadata_retries = plant.get("metadata_retries", 0)
        if not scientific_name or metadata_status not in ("pending", "error"):
            return
        if metadata_status == "error" and metadata_retries >= MAX_METADATA_RETRIES:
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
            plant["metadata_retries"] = metadata_retries + 1
            self.state.pokedex[plant["zh_name"]] = plant
            await save_cached_pokedex_debounced(self.state.pokedex)
