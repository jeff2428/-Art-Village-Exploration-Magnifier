from __future__ import annotations

from typing import Any

from config import (
    CAMERA_PREVIEW_SIZE,
    CAMERA_ZOOM_STEP,
    LENS_VIEWPORT_SIZE,
    MAX_CAMERA_ZOOM,
    MIN_CAMERA_ZOOM,
)


def clamp_camera_zoom(value: float) -> float:
    return min(MAX_CAMERA_ZOOM, max(MIN_CAMERA_ZOOM, round(value / CAMERA_ZOOM_STEP) * CAMERA_ZOOM_STEP))


def camera_preview_metrics(zoom_level: float) -> tuple[int, int, int]:
    zoom = clamp_camera_zoom(zoom_level)
    size = round(CAMERA_PREVIEW_SIZE * zoom)
    offset = round((LENS_VIEWPORT_SIZE - size) / 2)
    return size, offset, offset


def camera_descriptor_text(camera_description: Any) -> str:
    parts: list[str] = []
    if isinstance(camera_description, dict):
        parts.extend(str(value) for value in camera_description.values())
    else:
        for field in ("name", "label", "display_name", "description", "lens_direction", "position", "device_id"):
            try:
                value = getattr(camera_description, field)
            except AttributeError:
                value = None
            if value:
                parts.append(str(value))
    parts.append(str(camera_description))
    return " ".join(parts).lower()


def camera_direction_score(camera_description: Any, direction: str) -> int:
    text = camera_descriptor_text(camera_description)
    front_terms = ("front", "selfie", "user", "facetime", "前", "前置")
    back_terms = ("back", "rear", "environment", "world", "後", "後置", "主鏡頭")
    avoid_terms = ("ultra", "tele", "macro", "depth", "0.5", "2x", "超廣角", "望遠", "微距")
    main_terms = ("main", "primary", "default", "standard", "主", "主要")
    terms = front_terms if direction == "front" else back_terms
    score = 0
    if any(term in text for term in terms):
        score += 100
    if direction == "back" and any(term in text for term in main_terms):
        score += 20
    if any(term in text for term in avoid_terms):
        score -= 30
    return score


def select_preferred_cameras(available_cameras: list[Any]) -> list[Any]:
    if not available_cameras:
        return []
    back_candidates = [
        (camera_direction_score(camera_description, "back"), index, camera_description)
        for index, camera_description in enumerate(available_cameras)
    ]
    front_candidates = [
        (camera_direction_score(camera_description, "front"), index, camera_description)
        for index, camera_description in enumerate(available_cameras)
    ]
    back_score, _, back_camera = max(back_candidates, key=lambda item: (item[0], -item[1]))
    front_score, _, front_camera = max(front_candidates, key=lambda item: (item[0], -item[1]))
    selected: list[Any] = []
    if back_score > 0:
        selected.append(back_camera)
    if front_score > 0 and front_camera not in selected:
        selected.append(front_camera)
    if selected:
        return selected
    return [available_cameras[0]]
