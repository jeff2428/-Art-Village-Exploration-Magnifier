from __future__ import annotations

from typing import Callable, Optional

import flet as ft


Callback = Optional[Callable[[ft.ControlEvent], None]]


def border_all(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


class _PressableRoundButton(ft.GestureDetector):
    def __init__(
        self,
        label: str,
        icon: str,
        top: int,
        on_click: Callback,
        disabled: bool = False,
    ) -> None:
        self._button_face = ft.Container(
            width=86,
            height=86,
            tooltip=label,
            border_radius=43,
            alignment=ft.Alignment(0, 0),
            gradient=ft.RadialGradient(
                center=ft.Alignment(-0.38, -0.45),
                radius=0.95,
                colors=[
                    "#f2d5bf",
                    "#d9986b",
                    "#8a5335",
                    "#3f2013",
                ],
            ),
            border=border_all(3, "#3d1f11"),
            shadow=[
                ft.BoxShadow(
                    blur_radius=18,
                    spread_radius=1,
                    color="#6d000000",
                    offset=ft.Offset(0, 8),
                ),
                ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=-2,
                    color="#80ffffff",
                    offset=ft.Offset(-2, -2),
                ),
            ],
            animate_offset=ft.Animation(90, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                [
                    ft.Icon(icon, size=32, color="#2b1308"),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_900, color="#2b1308"),
                ],
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        super().__init__(
            left=17,
            top=top,
            mouse_cursor=ft.MouseCursor.FORBIDDEN if disabled else ft.MouseCursor.CLICK,
            content=self._button_face,
            on_tap=on_click if not disabled else None,
            on_tap_down=self._press if not disabled else None,
            on_tap_up=self._release if not disabled else None,
            on_tap_cancel=self._release if not disabled else None,
        )

    def _press(self, _event: ft.ControlEvent) -> None:
        self._button_face.offset = ft.Offset(0, 0.08)
        self._button_face.update()

    def _release(self, _event: ft.ControlEvent) -> None:
        self._button_face.offset = ft.Offset(0, 0)
        self._button_face.update()


class MagnifierHandle(ft.Stack):
    """Reusable storybook-style leather magnifier handle with two physical buttons."""

    def __init__(
        self,
        on_switch: Callback = None,
        on_capture: Callback = None,
        switch_enabled: bool = True,
        capture_enabled: bool = True,
    ) -> None:
        super().__init__(
            width=120,
            height=260,
            controls=[
                ft.Container(
                    left=0,
                    top=0,
                    width=120,
                    height=260,
                    border_radius=ft.BorderRadius(
                        top_left=60,
                        top_right=60,
                        bottom_left=28,
                        bottom_right=28,
                    ),
                    gradient=ft.RadialGradient(
                        center=ft.Alignment(-0.25, -0.85),
                        radius=1.32,
                        colors=[
                            "#7a4b38",
                            "#583527",
                            "#3a2118",
                            "#21110c",
                        ],
                    ),
                    border=border_all(4, "#1a0f0a"),
                    shadow=[
                        ft.BoxShadow(
                            blur_radius=26,
                            spread_radius=2,
                            color="#6b000000",
                            offset=ft.Offset(0, 12),
                        )
                    ],
                ),
                ft.Container(
                    left=13,
                    top=20,
                    width=94,
                    height=220,
                    border_radius=47,
                    border=border_all(3, "#8d6a58"),
                    opacity=0.55,
                ),
                *[
                    ft.Container(
                        left=55,
                        top=34 + index * 22,
                        width=10,
                        height=4,
                        border_radius=2,
                        bgcolor="#c59a7c88",
                    )
                    for index in range(9)
                ],
                _PressableRoundButton(
                    label="切換鏡頭" if switch_enabled else "無法切換",
                    icon=ft.Icons.CAMERASWITCH,
                    top=44,
                    on_click=on_switch,
                    disabled=not switch_enabled,
                ),
                _PressableRoundButton(
                    label="拍攝" if capture_enabled else "準備中",
                    icon=ft.Icons.CAMERA_ALT,
                    top=148,
                    on_click=on_capture,
                ),
            ],
        )
