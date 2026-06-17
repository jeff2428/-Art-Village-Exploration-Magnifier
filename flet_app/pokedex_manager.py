from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from config import POKEDEX_SAVE_DEBOUNCE_DELAY, MAX_POKEDEX_STORAGE_BYTES
from services.indexed_db import indexed_db
from services.lru_cache import lru_cache_manager

POKEDEX_STORAGE_KEY = "artVillagePokedex"
THEME_STORAGE_KEY = "artVillageDarkMode"
LOCAL_CACHE_DIR = Path(tempfile.gettempdir()) / "art-village-exploration-magnifier"
LOCAL_CACHE_PATH = LOCAL_CACHE_DIR / "local_pokedex_cache.json"


def _entry_to_animal(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "animal",
        "emoji": entry.get("emoji", "🐾"),
        "role": entry.get("role", ""),
        "desc": entry.get("desc", ""),
        "portrait": entry.get("portrait", ""),
        "photos": entry.get("photos", []),
    }


def _animals_payload_to_db(payload: Any) -> tuple[bool, dict[str, dict[str, Any]]]:
    if not isinstance(payload, dict):
        return False, {}
    animals_list = payload.get("animals")
    if not isinstance(animals_list, list):
        return False, {}

    db: dict[str, dict[str, Any]] = {}
    for entry in animals_list:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        if name:
            db[name] = _entry_to_animal(entry)
    return True, db


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
        _valid, db = _animals_payload_to_db(data)
        if db:
            return db
    except (OSError, json.JSONDecodeError, StopIteration):
        pass
    return {}


DEFAULT_ANIMALS: dict[str, dict[str, Any]] = {
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

ANIMALS_DB: dict[str, dict[str, Any]] = load_animals_db() or DEFAULT_ANIMALS


async def _preload_animals_from_idb() -> None:
    """Background preload animals from IndexedDB into ANIMALS_DB global."""
    try:
        cached = await indexed_db.get("pokedex", "artVillageAnimals")
        if cached and isinstance(cached, dict):
            valid, db = _animals_payload_to_db(cached)
            if valid:
                global ANIMALS_DB
                ANIMALS_DB = db
    except Exception as exc:
        logger.debug("IndexedDB animals preload failed: %s", exc)


def load_animals_db_dynamic() -> dict[str, dict[str, Any]]:
    """Load animals DB from in-memory cache (sync).

    For async IndexedDB loading, use _preload_animals_from_idb() on startup.
    Sync callers always get the current ANIMALS_DB global value.
    """
    return ANIMALS_DB



async def _cache_get(key: str) -> str | None:
    """Get from Service Worker Cache API (fast, browser-only)."""
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
    """Write to Service Worker Cache API (fast, browser-only)."""
    try:
        from js import Response as JsResponse
        from js import caches as js_caches  # type: ignore

        cache = await js_caches.open("art-village-pokedex")
        await cache.put(key, JsResponse.new(value, {"headers": {"Content-Type": "application/json"}}))
    except (ImportError, AttributeError, TypeError):
        pass


async def load_json_cache(storage_key: str, fallback: Any) -> Any:
    """Load JSON data with IndexedDB primary + Service Worker Cache secondary.

    Priority order:
      1. In-memory LRU cache (fastest, survives page reload for active images)
      2. IndexedDB (primary persistent store, ~50MB+)
      3. Service Worker Cache API (secondary persistent store)
      4. Fallback value
    """
    # Check in-memory LRU cache first
    lru_key = f"json_{storage_key}"
    cached = await lru_cache_manager.get(lru_key)
    if cached is not None:
        return cached

    # Try IndexedDB (primary persistent store)
    try:
        idb_value = await indexed_db.get("pokedex", storage_key)
        if idb_value is not None:
            # Re-populate LRU cache for future fast access
            await lru_cache_manager.set(lru_key, idb_value)
            return idb_value
    except Exception as exc:
        logger.debug("IndexedDB get failed for %s: %s", storage_key, exc)

    # Fallback to Service Worker Cache API
    raw = await _cache_get(storage_key)
    if raw:
        try:
            data = json.loads(raw)
            # Store in IndexedDB and LRU cache for future reads
            await indexed_db.put("pokedex", storage_key, data)
            await lru_cache_manager.set(lru_key, data)
            return data
        except json.JSONDecodeError:
            pass

    return fallback


async def save_json_cache(storage_key: str, data: Any) -> None:
    """Save JSON data to IndexedDB (primary) + Service Worker Cache (secondary).

    Also stores in LRU cache for immediate subsequent reads.
    """
    serialized = json.dumps(data, ensure_ascii=False)
    lru_key = f"json_{storage_key}"

    # Write to IndexedDB (primary persistent store)
    try:
        await indexed_db.put("pokedex", storage_key, data)
    except Exception as exc:
        logger.warning("IndexedDB save failed for %s: %s", storage_key, exc)

    # Write to Service Worker Cache API (secondary, fast repeat reads)
    await _cache_set(storage_key, serialized)

    # Update LRU cache for immediate subsequent reads
    await lru_cache_manager.set(lru_key, data, size_bytes=len(serialized.encode("utf-8")))


def validate_pokedex_size(pokedex: dict[str, dict[str, Any]]) -> int | None:
    serialized = json.dumps(pokedex, ensure_ascii=False)
    size = len(serialized.encode("utf-8"))
    return size if size > MAX_POKEDEX_STORAGE_BYTES else None


async def save_cached_pokedex(pokedex: dict[str, dict[str, Any]]) -> None:
    for _ in range(5):
        oversize = validate_pokedex_size(pokedex)
        if not oversize:
            break
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


def _image_hash(src: str) -> str:
    """Generate a short hash key for image storage."""
    import hashlib
    return f"img_{hashlib.md5(src.encode('utf-8')).hexdigest()[:12]}"


async def _store_image_in_idb(src: str) -> None:
    """Store base64 image data in IndexedDB images store (keyed by hash)."""
    if not src or len(src) < 100:
        return  # Skip small/non-image strings
    try:
        img_key = _image_hash(src)
        await indexed_db.put("images", img_key, src)
    except Exception as exc:
        logger.debug("IndexedDB image store failed for hash %s: %s", _image_hash(src)[:8], exc)


async def _restore_image_from_idb(src_ref: str) -> str:
    """Restore base64 image data from IndexedDB images store or LRU cache."""
    if not src_ref or len(src_ref) < 100:
        return src_ref  # Not a base64 image, return as-is

    img_key = _image_hash(src_ref)

    # Check LRU cache first (fastest)
    cached = await lru_cache_manager.get(f"idb_img_{img_key}")
    if cached is not None:
        return cached  # type: ignore[return-value]

    # Try IndexedDB images store
    try:
        data = await indexed_db.get("images", img_key)
        if data and isinstance(data, str):
            # Populate LRU cache for future reads
            await lru_cache_manager.set(f"idb_img_{img_key}", data, size_bytes=len(data.encode("utf-8")))
            return data
    except Exception as exc:
        logger.debug("IndexedDB image restore failed for hash %s: %s", img_key[:8], exc)

    return src_ref  # Return original if not found


async def _compress_pokedex_for_storage(pokedex: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
    """Compress pokedex for storage by moving images to IndexedDB.

    Returns (compressed_pokedex, image_refs) where image_refs is a list of
    (img_key, original_src) tuples for storing in IndexedDB.
    Images are replaced with hash references in the pokedex entry.
    """
    compressed = {}
    image_refs: list[tuple[str, str]] = []

    for name, entry in pokedex.items():
        if not isinstance(entry, dict):
            compressed[name] = entry
            continue

        new_entry = dict(entry)
        captured = new_entry.get("captured_image", {})
        src = captured.get("src", "") if isinstance(captured, dict) else ""

        if src and len(src) >= 100:
            img_key = _image_hash(src)
            new_entry["captured_image"] = {"src": img_key, "label": captured.get("label", ""), "_is_ref": True}
            image_refs.append((img_key, src))
        else:
            new_entry["captured_image"] = captured

        compressed[name] = new_entry

    return compressed, image_refs


async def _decompress_pokedex_for_display(pokedex: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Restore full image data from references for display."""
    result = {}

    for name, entry in pokedex.items():
        if not isinstance(entry, dict):
            result[name] = entry
            continue

        new_entry = dict(entry)
        captured = new_entry.get("captured_image", {})
        src_ref = captured.get("src", "") if isinstance(captured, dict) else ""

        if src_ref and len(src_ref) >= 100 and captured.get("_is_ref"):
            full_src = await _restore_image_from_idb(src_ref)
            new_entry["captured_image"] = {"src": full_src, "label": captured.get("label", "")}

        result[name] = new_entry

    return result


async def save_cached_pokedex(pokedex: dict[str, dict[str, Any]]) -> None:
    """Save pokedex to IndexedDB with image compression."""
    for _ in range(5):
        oversize = validate_pokedex_size(pokedex)
        if not oversize:
            break
        trim_pokedex_images(pokedex)

    # Compress images before storage
    compressed, image_refs = await _compress_pokedex_for_storage(pokedex)
    await save_json_cache(POKEDEX_STORAGE_KEY, compressed)

    # Store images in IndexedDB (separate store for better management)
    for img_key, original_src in image_refs:
        try:
            await indexed_db.put("images", img_key, original_src)
        except Exception as exc:
            logger.warning("IndexedDB image store failed for %s: %s", img_key[:8], exc)


async def load_cached_pokedex() -> dict[str, dict[str, Any]]:
    """Load pokedex from IndexedDB with image restoration."""
    cached = await load_json_cache(POKEDEX_STORAGE_KEY, {})
    if not isinstance(cached, dict):
        return {}

    # Restore full image data for display
    try:
        restored = await _decompress_pokedex_for_display(cached)
        return restored
    except Exception as exc:
        logger.debug("Image decompression failed, returning raw cache: %s", exc)
        return cached


async def load_dark_mode_preference() -> bool:
    val = await load_json_cache(THEME_STORAGE_KEY, None)
    if val is True or val == "true":
        return True
    return False


async def save_dark_mode_preference(is_dark: bool) -> None:
    await save_json_cache(THEME_STORAGE_KEY, "true" if is_dark else "false")


async def clear_legacy_snapshot_cache() -> None:
    """Clear legacy snapshot data from IndexedDB."""
    try:
        await indexed_db.delete("pokedex", "artVillageSnapshotQueue")
    except Exception as exc:
        logger.debug("IndexedDB clear legacy snapshot failed: %s", exc)
    # Also clean up file system cache
    try:
        legacy_path = LOCAL_CACHE_DIR / "local_snapshot_queue.json"
        if legacy_path.exists():
            legacy_path.unlink()
    except OSError:
        pass


class _DebouncedSaver:
    """Debounced saver for pokedex to batch rapid updates."""

    def __init__(self, delay: float = POKEDEX_SAVE_DEBOUNCE_DELAY) -> None:
        self._delay = delay
        self._task: asyncio.Task | None = None
        self._pending_data: dict[str, dict[str, Any]] | None = None
        self._lock = asyncio.Lock()

    async def schedule_save(self, pokedex: dict[str, dict[str, Any]]) -> None:
        self._pending_data = pokedex
        if self._task is not None:
            async with self._lock:
                self._task.cancel()
        self._task = asyncio.create_task(self._run_save())

    async def _run_save(self) -> None:
        try:
            await asyncio.sleep(self._delay)
            async with self._lock:
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
        async with self._lock:
            if self._pending_data is not None:
                await save_cached_pokedex(self._pending_data)


_debounced_saver = _DebouncedSaver(delay=0.5)


async def save_cached_pokedex_debounced(pokedex: dict[str, dict[str, Any]]) -> None:
    """Save pokedex with debouncing to batch rapid updates."""
    await _debounced_saver.schedule_save(pokedex)


async def flush_pokedex_save() -> None:
    """Force flush any pending pokedex save."""
    await _debounced_saver.flush()


async def sync_animals_from_worker() -> None:
    """Fetch animals config from worker and save to IndexedDB + in-memory DB."""
    try:
        from build_config import WORKER_URL
    except (ImportError, AttributeError):
        WORKER_URL = "https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev"  # noqa: N806

    if "YOUR-WORKER" in WORKER_URL:
        return

    try:
        from js import fetch  # type: ignore
        response = await fetch(f"{WORKER_URL.rstrip('/')}/animals")
        if response.ok:
            text = await response.text()
            data = json.loads(text)
            if "animals" in data:
                # Save to IndexedDB (primary persistent store)
                await indexed_db.put("pokedex", "artVillageAnimals", data)

                # Update in-memory DB as well
                global ANIMALS_DB
                valid, db = _animals_payload_to_db(data)
                if valid:
                    ANIMALS_DB = db
    except (ImportError, ModuleNotFoundError):
        # Fallback for desktop mode
        def _sync_sync():
            try:
                with urllib.request.urlopen(f"{WORKER_URL.rstrip('/')}/animals", timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                if "animals" in data:
                    cache_path = LOCAL_CACHE_DIR / "animals_cache.json"
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

                    # Update in-memory DB
                    global ANIMALS_DB
                    valid, db = _animals_payload_to_db(data)
                    if valid:
                        ANIMALS_DB = db
            except Exception:
                pass

        await asyncio.to_thread(_sync_sync)
