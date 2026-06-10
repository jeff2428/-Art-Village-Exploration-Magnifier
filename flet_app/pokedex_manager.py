from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any

POKEDEX_STORAGE_KEY = "artVillagePokedex"
THEME_STORAGE_KEY = "artVillageDarkMode"
LOCAL_CACHE_DIR = Path(tempfile.gettempdir()) / "art-village-exploration-magnifier"
LOCAL_CACHE_PATH = LOCAL_CACHE_DIR / "local_pokedex_cache.json"


def load_animals_db() -> dict[str, dict[str, Any]]:
    module_dir = Path(__file__).resolve().parent
    candidates = (
        module_dir / "admin" / "animals.json",
        module_dir.parent / "admin" / "animals.json",
    )
    try:
        json_path = next(path for path in candidates if path.exists())
        raw = json_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        animals_list = data.get("animals", [])
        db: dict[str, dict[str, Any]] = {}
        for entry in animals_list:
            name = entry.get("name", "")
            if name:
                db[name] = {
                    "type": "animal",
                    "emoji": entry.get("emoji", "🐾"),
                    "role": entry.get("role", ""),
                    "desc": entry.get("desc", ""),
                    "portrait": entry.get("portrait", ""),
                    "photos": entry.get("photos", []),
                }
        if db:
            return db
    except (OSError, json.JSONDecodeError, StopIteration):
        pass
    return {}


_DEFAULT_ANIMALS: dict[str, dict[str, Any]] = {
    "貝貝": {
        "type": "animal", "emoji": "🐶", "role": "溫柔導覽員",
        "desc": "東北角的米克斯母狗，也是藝素村最溫柔的導嚮員。",
    },
    "牧耳": {
        "type": "animal", "emoji": "🐕", "role": "草地巡邏員",
        "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。",
    },
    "小飛俠": {
        "type": "animal", "emoji": "🐈", "role": "屋頂觀察員",
        "desc": "身手矯健，總是在屋頂上觀察探險家們。",
    },
    "嘿皮": {
        "type": "animal", "emoji": "🐈‍⬛", "role": "親人接待員",
        "desc": "個性大方的黑貓，討摸是牠的日常。",
    },
    "冬瓜": {
        "type": "animal", "emoji": "🐱", "role": "慵懶守護者",
        "desc": "圓滾滾的橘貓，是村裡的慵懶大王。",
    },
}

ANIMALS_DB: dict[str, dict[str, Any]] = load_animals_db() or _DEFAULT_ANIMALS


def load_animals_db_dynamic() -> dict[str, dict[str, Any]]:
    try:
        from js import localStorage
        stored = localStorage.getItem("artVillageAnimals")
        if stored:
            data = json.loads(stored)
            animals_list = data.get("animals", [])
            db: dict[str, dict[str, Any]] = {}
            for entry in animals_list:
                name = entry.get("name", "")
                if name:
                    db[name] = {
                        "type": "animal",
                        "emoji": entry.get("emoji", "🐾"),
                        "role": entry.get("role", ""),
                        "desc": entry.get("desc", ""),
                        "portrait": entry.get("portrait", ""),
                        "photos": entry.get("photos", []),
                    }
            if db:
                return db
    except (ImportError, json.JSONDecodeError, AttributeError):
        pass

    static_db = load_animals_db()
    if static_db:
        return static_db

    return _DEFAULT_ANIMALS



async def _cache_get(key: str) -> str | None:
    try:
        from js import caches as js_caches  # type: ignore

        cache = await js_caches.open("art-village-pokedex")
        response = await cache.match(key)
        if response is None:
            return None
        return await response.text()
    except (ImportError, AttributeError, TypeError):
        return None


async def _cache_set(key: str, value: str) -> None:
    try:
        from js import Response as JsResponse
        from js import caches as js_caches  # type: ignore

        cache = await js_caches.open("art-village-pokedex")
        await cache.put(key, JsResponse.new(value, {"headers": {"Content-Type": "application/json"}}))
    except (ImportError, AttributeError, TypeError):
        pass


async def load_json_cache(storage_key: str, fallback: Any) -> Any:
    raw = await _cache_get(storage_key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    try:
        from js import localStorage  # type: ignore

        raw = localStorage.getItem(storage_key)
        if raw:
            return json.loads(raw)
    except (ImportError, json.JSONDecodeError, AttributeError):
        pass
    return fallback


async def save_json_cache(storage_key: str, data: Any) -> None:
    serialized = json.dumps(data, ensure_ascii=False)
    await _cache_set(storage_key, serialized)
    try:
        from js import localStorage  # type: ignore

        localStorage.setItem(storage_key, serialized)
    except (ImportError, AttributeError, TypeError):
        pass


def validate_pokedex_size(pokedex: dict[str, dict[str, Any]]) -> int | None:
    serialized = json.dumps(pokedex, ensure_ascii=False)
    size = len(serialized.encode("utf-8"))
    return size if size > 50_000_000 else None


async def save_cached_pokedex(pokedex: dict[str, dict[str, Any]]) -> None:
    for _ in range(3):
        oversize = validate_pokedex_size(pokedex)
        if not oversize:
            await save_json_cache(POKEDEX_STORAGE_KEY, pokedex)
            return
        trim_pokedex_images(pokedex)
    await save_json_cache(POKEDEX_STORAGE_KEY, pokedex)


def trim_pokedex_images(pokedex: dict[str, dict[str, Any]]) -> None:
    if not pokedex:
        return
    items_with_images = [
        (name, entry) for name, entry in pokedex.items()
        if isinstance(entry, dict) and entry.get("captured_image", {}).get("src")
    ]
    if not items_with_images:
        return
    items_with_images.sort(key=lambda x: len(x[1].get("captured_image", {}).get("src", "")))
    name, entry = items_with_images[-1]
    entry["captured_image"] = {"src": "", "label": "照片已移除（容量不足）"}


async def load_cached_pokedex() -> dict[str, dict[str, Any]]:
    cached = await load_json_cache(POKEDEX_STORAGE_KEY, {})
    return cached if isinstance(cached, dict) else {}


async def load_dark_mode_preference() -> bool:
    val = await load_json_cache(THEME_STORAGE_KEY, None)
    if val is True or val == "true":
        return True
    return False


async def save_dark_mode_preference(is_dark: bool) -> None:
    await save_json_cache(THEME_STORAGE_KEY, "true" if is_dark else "false")


def clear_legacy_snapshot_cache() -> None:
    try:
        from js import localStorage  # type: ignore

        localStorage.removeItem("artVillageSnapshotQueue")
    except (ImportError, AttributeError, TypeError):
        pass
    try:
        legacy_path = LOCAL_CACHE_DIR / "local_snapshot_queue.json"
        if legacy_path.exists():
            legacy_path.unlink()
    except OSError:
        pass


class _DebouncedSaver:
    """Debounced saver for pokedex to batch rapid updates."""

    def __init__(self, delay: float = 0.5) -> None:
        self._delay = delay
        self._task: asyncio.Task | None = None
        self._pending_data: dict[str, dict[str, Any]] | None = None

    def schedule_save(self, pokedex: dict[str, dict[str, Any]]) -> None:
        self._pending_data = pokedex
        if self._task is not None:
            self._task.cancel()
        self._task = asyncio.create_task(self._run_save())

    async def _run_save(self) -> None:
        try:
            await asyncio.sleep(self._delay)
            if self._pending_data is not None:
                await save_cached_pokedex(self._pending_data)
        except asyncio.CancelledError:
            pass
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        finally:
            self._task = None

    async def flush(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._pending_data is not None:
            await save_cached_pokedex(self._pending_data)


_debounced_saver = _DebouncedSaver(delay=0.5)


async def save_cached_pokedex_debounced(pokedex: dict[str, dict[str, Any]]) -> None:
    """Save pokedex with debouncing to batch rapid updates."""
    _debounced_saver.schedule_save(pokedex)


async def flush_pokedex_save() -> None:
    """Force flush any pending pokedex save."""
    await _debounced_saver.flush()
