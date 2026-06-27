"""IndexedDB wrapper for Art Village Exploration Magnifier.

Replaces localStorage with IndexedDB for persistent browser storage.
Provides async operations, structured data support, and much larger quota (~50MB+).

Usage:
    from services.indexed_db import indexed_db
    await indexed_db.put("artVillagePokedex", pokedex_data)
    data = await indexed_db.get("artVillagePokedex")
"""

from __future__ import annotations

import asyncio
import json
import logging
from types import ModuleType
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

_js: ModuleType | None
try:
    import js as _js  # type: ignore[import-not-found]
except ImportError:
    _js = None

# IndexedDB constants
IDB_NAME = "ArtVillageMagnifier"
IDB_VERSION = 2
STORE_POKEDEX = "pokedex"
STORE_IMAGES = "images"
STORE_META = "meta"


class IndexedDBError(Exception):
    """IndexedDB operation failed."""


class _IndexedDB:
    """Async wrapper around browser IndexedDB API via js/evalJS bridge."""

    def __init__(self) -> None:
        self._db: Any | None = None
        self._ready_event = asyncio.Event()
        self._init_task: asyncio.Task | None = None

    async def _ensure_init(self) -> None:
        """Initialize IndexedDB connection if not already done."""
        if self._db is not None:
            return
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._open_db())
        try:
            await self._init_task
        except Exception as exc:
            logger.warning("IndexedDB initialization failed: %s", exc)
            raise IndexedDBError(f"Failed to open IndexedDB: {exc}") from exc

    async def _open_db(self) -> None:
        """Open or create the IndexedDB database."""
        try:
            # Import js module for browser environment
            import js  # type: ignore[import-not-found]
        except ImportError:
            logger.debug("js module not available (desktop mode), skipping IndexedDB")
            self._db = None
            self._ready_event.set()
            return

        try:
            # Use evalJS to interact with IndexedDB since js.IDBRequest etc. may not be typed
            result = await js.evalJS(f"""
                (() => {{
                    return new Promise((resolve, reject) => {{
                        const request = indexedDB.open('{IDB_NAME}', {IDB_VERSION});

                        request.onupgradeneeded = (event) => {{
                            const db = event.target.result;
                            if (!db.objectStoreNames.contains('{STORE_POKEDEX}')) {{
                                db.createObjectStore('{STORE_POKEDEX}', {{ keyPath: 'key' }});
                            }}
                            if (!db.objectStoreNames.contains('{STORE_IMAGES}')) {{
                                db.createObjectStore('{STORE_IMAGES}', {{ keyPath: 'key' }});
                            }}
                            if (!db.objectStoreNames.contains('{STORE_META}')) {{
                                db.createObjectStore('{STORE_META}', {{ keyPath: 'key' }});
                            }}
                            // Migration v1 -> v2: add animals store
                            if (db.version <= 1 && !db.objectStoreNames.contains('animals')) {{
                                db.createObjectStore('animals', {{ keyPath: 'name' }});
                            }}
                        }};

                        request.onsuccess = (event) => {{
                            resolve(event.target.result);
                        }};

                        request.onerror = (event) => {{
                            reject(new Error('IndexedDB open error: ' + event.target.errorCode));
                        }};
                    }});
                }})()
            """)

            self._db = result
            logger.info("IndexedDB '%s' opened successfully", IDB_NAME)

        except Exception as exc:
            logger.warning("IndexedDB open failed, falling back to localStorage: %s", exc)
            self._db = None

        finally:
            self._ready_event.set()

    async def put(self, store_name: str, key: str, value: Any) -> None:
        """Store a value in an IndexedDB object store.

        Args:
            store_name: Object store name (pokedex, images, or meta).
            key: Unique key for the entry.
            value: Data to store (will be JSON-serialized if not bytes).
        """
        await self._ensure_init()
        if self._db is None:
            # Fallback to localStorage
            await self._put_localstorage(store_name, key, value)
            return

        try:
            serialized = (
                json.dumps(value, ensure_ascii=False)
                if not isinstance(value, bytes)
                else value.decode("utf-8", errors="replace")
            )
            assert _js is not None

            await _js.evalJS(f"""
                (() => {{
                    return new Promise((resolve, reject) => {{
                        const db = {repr(self._db)};
                        const tx = db.transaction('{store_name}', 'readwrite');
                        const store = tx.objectStore('{store_name}');
                        const safeKey = decodeURIComponent('{quote(key)}');
                        const request = store.put({{ key: safeKey, value: `{serialized}` }});

                        request.onsuccess = () => resolve(true);
                        request.onerror = (e) => reject(e.target.error);
                        tx.oncomplete = () => resolve(true);
                        tx.onerror = (e) => reject(e.target.error);
                    }});
                }})()
            """)

        except Exception as exc:
            logger.warning("IndexedDB put failed for %s/%s, falling back: %s", store_name, key, exc)
            await self._put_localstorage(store_name, key, value)

    async def get(self, store_name: str, key: str) -> Any | None:
        """Retrieve a value from an IndexedDB object store.

        Args:
            store_name: Object store name (pokedex, images, or meta).
            key: Key to look up.

        Returns:
            The stored value, or None if not found.
        """
        await self._ensure_init()
        if self._db is None:
            return await self._get_localstorage(store_name, key)

        try:
            assert _js is not None
            result = await _js.evalJS(f"""
                (() => {{
                    return new Promise((resolve, reject) => {{
                        const db = {repr(self._db)};
                        const tx = db.transaction('{store_name}', 'readonly');
                        const store = tx.objectStore('{store_name}');
                        const safeKey = decodeURIComponent('{quote(key)}');
                        const request = store.get(safeKey);

                        request.onsuccess = (event) => {{
                            const entry = event.target.result;
                            resolve(entry ? entry.value : null);
                        }};
                        request.onerror = (e) => reject(e.target.error);
                    }});
                }})()
            """)

            return result  # type: ignore[return-value]

        except Exception as exc:
            logger.warning("IndexedDB get failed for %s/%s, falling back: %s", store_name, key, exc)
            return await self._get_localstorage(store_name, key)

    async def delete(self, store_name: str, key: str) -> None:
        """Delete an entry from an IndexedDB object store.

        Args:
            store_name: Object store name (pokedex, images, or meta).
            key: Key to delete.
        """
        await self._ensure_init()
        if self._db is None:
            await self._delete_localstorage(store_name, key)
            return

        try:
            assert _js is not None
            await _js.evalJS(f"""
                (() => {{
                    return new Promise((resolve, reject) => {{
                        const db = {repr(self._db)};
                        const tx = db.transaction('{store_name}', 'readwrite');
                        const store = tx.objectStore('{store_name}');
                        const safeKey = decodeURIComponent('{quote(key)}');
                        const request = store.delete(safeKey);

                        request.onsuccess = () => resolve(true);
                        request.onerror = (e) => reject(e.target.error);
                        tx.oncomplete = () => resolve(true);
                        tx.onerror = (e) => reject(e.target.error);
                    }});
                }})()
            """)

        except Exception as exc:
            logger.warning("IndexedDB delete failed for %s/%s, falling back: %s", store_name, key, exc)
            await self._delete_localstorage(store_name, key)

    async def clear_store(self, store_name: str) -> None:
        """Clear all entries from an IndexedDB object store.

        Args:
            store_name: Object store name (pokedex, images, or meta).
        """
        await self._ensure_init()
        if self._db is None:
            # localStorage doesn't support per-store clear, use delete_all
            await self.delete_all(store_name)
            return

        try:
            assert _js is not None
            await _js.evalJS(f"""
                (() => {{
                    return new Promise((resolve, reject) => {{
                        const db = {repr(self._db)};
                        const tx = db.transaction('{store_name}', 'readwrite');
                        const store = tx.objectStore('{store_name}');
                        const request = store.clear();

                        request.onsuccess = () => resolve(true);
                        request.onerror = (e) => reject(e.target.error);
                    }});
                }})()
            """)

        except Exception as exc:
            logger.warning("IndexedDB clear_store failed for %s, falling back: %s", store_name, exc)
            await self.delete_all(store_name)

    async def delete_all(self, store_name: str) -> None:
        """Delete all entries from a store (fallback for localStorage).

        Args:
            store_name: Store name prefix used in localStorage keys.
        """
        try:
            import js  # type: ignore[import-not-found]
            await js.evalJS(f"""
                (() => {{
                    const prefix = '{store_name}_';
                    const keysToRemove = [];
                    for (let i = localStorage.length - 1; i >= 0; i--) {{
                        const key = localStorage.key(i);
                        if (key && key.startsWith(prefix)) {{
                            keysToRemove.push(key);
                        }}
                    }}
                    keysToRemove.forEach(k => localStorage.removeItem(k));
                }})()
            """)
        except Exception as exc:
            logger.warning("delete_all fallback failed for %s: %s", store_name, exc)

    async def _put_localstorage(self, store_name: str, key: str, value: Any) -> None:
        """Fallback: store in localStorage with prefixed key."""
        try:
            import js  # type: ignore[import-not-found]
            serialized = json.dumps(value, ensure_ascii=False) if not isinstance(value, bytes) else value.decode("utf-8", errors="replace")  # noqa: E501
            await js.evalJS(f"""
                (() => {{ localStorage.setItem('{store_name}_{quote(key)}', `{serialized}`); }})()
            """)
        except Exception as exc:
            logger.warning("localStorage put failed for %s/%s: %s", store_name, key, exc)

    async def _get_localstorage(self, store_name: str, key: str) -> Any | None:
        """Fallback: retrieve from localStorage with prefixed key."""
        try:
            import js  # type: ignore[import-not-found]
            result = await js.evalJS(f"""
                (() => {{
                    const val = localStorage.getItem('{store_name}_{quote(key)}');
                    return val;
                }})()
            """)
            if result is None or result == "null":
                return None
            try:
                return json.loads(result)
            except (json.JSONDecodeError, TypeError):
                return result
        except Exception as exc:
            logger.warning("localStorage get failed for %s/%s: %s", store_name, key, exc)
            return None

    async def _delete_localstorage(self, store_name: str, key: str) -> None:
        """Fallback: delete from localStorage with prefixed key."""
        try:
            import js  # type: ignore[import-not-found]
            await js.evalJS(f"""
                (() => {{ localStorage.removeItem('{store_name}_{quote(key)}'); }})()
            """)
        except Exception as exc:
            logger.warning("localStorage delete failed for %s/%s: %s", store_name, key, exc)

    async def close(self) -> None:
        """Close the IndexedDB connection."""
        if self._db is not None:
            try:
                import js  # type: ignore[import-not-found]
                await js.evalJS(f"""
                    (() => {{ {repr(self._db)}.close(); }})()
                """)
            except Exception as exc:
                logger.warning("IndexedDB close failed: %s", exc)
            self._db = None


# Module-level singleton
indexed_db = _IndexedDB()
