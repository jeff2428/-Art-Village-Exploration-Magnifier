from __future__ import annotations

import asyncio
from typing import Any

import flet as ft
from components.illustrations import MAGNIFYING_GLASS
from pokedex_manager import _DEFAULT_ANIMALS, load_animals_db_dynamic, save_cached_pokedex_debounced
from ui_theme import THEME
from views.gallery import build_gallery_card


class GalleryService:
    def __init__(
        self,
        page: ft.Page,
        state,
        status_text: ft.Text,
        create_background_task,
        show_gallery_card=None,
        close_dialog=None,
    ):
        self.page = page
        self.state = state
        self.status_text = status_text
        self.create_background_task = create_background_task
        self.show_gallery_card = show_gallery_card
        self.close_dialog = close_dialog

        self.grid = ft.GridView(
            expand=False, max_extent=180, child_aspect_ratio=2.8,
            spacing=10, run_spacing=10, height=260,
        )
        self.gallery_empty_state = ft.Container(
            height=160,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.Text(MAGNIFYING_GLASS, size=48, text_align=ft.TextAlign.CENTER),
                    ft.Text("尚無收藏", size=18, weight=ft.FontWeight.W_900, color=THEME["TITLE"],
                           text_align=ft.TextAlign.CENTER),
                    ft.Text("拍攝植物或認識動物後，\n收藏會自動出現在這裡", size=13, color=THEME["MUTED"],
                           text_align=ft.TextAlign.CENTER),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )
        self._gallery_card_map: dict[str, ft.Container] = {}

    def _build_gallery_card(self, name: str, item: dict[str, Any]) -> ft.Container:
        return build_gallery_card(
            name,
            item,
            on_click=lambda item_name, item_data: (
                self.show_gallery_card(item_name, item_data)
                if self.show_gallery_card
                else None
            ),
            on_delete=lambda item_name: self.confirm_delete(item_name, self.close_dialog),
        )

    def refresh(self, update_page: bool = True) -> None:
        new_cards: list[tuple[str, ft.Container]] = []
        for name in list(self._gallery_card_map):
            if name not in self.state.pokedex:
                card = self._gallery_card_map.pop(name)
                if card in self.grid.controls:
                    self.grid.controls.remove(card)
        for name, item in self.state.pokedex.items():
            if name in self._gallery_card_map:
                continue
            card = self._build_gallery_card(name, item)
            card.opacity = 0
            card.offset = ft.Offset(0, 0.3)
            card.animate_opacity = ft.Animation(duration=260,
                                                curve=ft.AnimationCurve.EASE_OUT)
            card.animate_offset = ft.Animation(duration=320,
                                               curve=ft.AnimationCurve.EASE_OUT)
            self._gallery_card_map[name] = card
            self.grid.controls.append(card)
            new_cards.append((name, card))
        has_items = bool(self.state.pokedex)
        self.grid.visible = has_items
        self.gallery_empty_state.visible = not has_items
        self.create_background_task(save_cached_pokedex_debounced(self.state.pokedex))
        if update_page:
            self.grid.update()
            if self.gallery_empty_state.page is not None:
                self.gallery_empty_state.update()
        if new_cards:
            self.create_background_task(self._animate_new_cards(new_cards))

    async def _animate_new_cards(
        self, new_cards: list[tuple[str, ft.Container]]
    ) -> None:
        await asyncio.sleep(0.05)
        for _, card in new_cards:
            card.opacity = 1.0
            card.offset = ft.Offset(0, 0)
            if card.page is not None:
                card.update()
            await asyncio.sleep(0.06)

    def add_plant(self, plant: dict[str, Any]) -> None:
        self.state.pokedex[plant["zh_name"]] = plant
        if plant.get("is_low_confidence", False):
            self.status_text.value = f"⚠️ {plant['zh_name']}（信心度低，建議確認）"
        else:
            self.status_text.value = (
                f"辨識成功：{plant['zh_name']} · {plant.get('confidence', 0)}%"
            )
        self.refresh()

    def add_animal(self, name: str) -> None:
        animals_db = load_animals_db_dynamic()
        data = animals_db.get(name) or _DEFAULT_ANIMALS.get(name, {})
        self.state.pokedex[name] = {"zh_name": name, **data}
        self.status_text.value = f"已遇見：{name}"
        self.refresh()

    def delete_item(self, name: str) -> None:
        if name in self.state.pokedex:
            self.state.pokedex.pop(name)
            self.create_background_task(save_cached_pokedex_debounced(self.state.pokedex))
            self.status_text.value = f"已刪除：{name}"
            self.refresh()
        self.page.pop_dialog()
        self.page.update()

    def clear_all(self) -> None:
        self.state.pokedex.clear()
        self._gallery_card_map.clear()
        self.grid.controls.clear()
        self.create_background_task(save_cached_pokedex_debounced(self.state.pokedex))
        self.status_text.value = "已清除探險圖鑑"
        self.page.pop_dialog()
        self.page.update()

    def confirm_delete(self, name: str, close_dialog) -> None:
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("刪除圖鑑卡片", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text(
                    f"要從探險圖鑑刪除「{name}」嗎？", size=15, color=THEME["TITLE"]
                ),
                actions=[
                    ft.TextButton("取消", on_click=close_dialog),
                    ft.TextButton(
                        "刪除",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda _event: self.delete_item(name),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        self.page.update()

    def confirm_clear(self) -> None:
        if not self.state.pokedex:
            self.status_text.value = "探險圖鑑目前是空的"
            self.page.update()
            return
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("清除探險圖鑑", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text(
                    "要刪除所有圖鑑卡片嗎？這個動作無法復原。",
                    size=15, color=THEME["TITLE"],
                ),
                actions=[
                    ft.TextButton("取消", on_click=self.close_dialog),
                    ft.TextButton(
                        "全部清除",
                        icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                        on_click=lambda _event: self.clear_all(),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        self.page.update()
