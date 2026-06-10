from __future__ import annotations

from typing import Any


class _Window:
    pass


class _Performance:
    def mark(self, _name: str) -> None:
        return None


class _LocalStorage:
    def getItem(self, _key: str) -> None:
        return None

    def setItem(self, _key: str, _value: str) -> None:
        return None

    def removeItem(self, _key: str) -> None:
        return None


class _Cache:
    async def match(self, _key: str) -> None:
        return None

    async def put(self, _key: str, _response: Any) -> None:
        return None


class _Caches:
    async def open(self, _name: str) -> _Cache:
        return _Cache()


class Response:
    @classmethod
    def new(cls, value: str, _options: dict[str, Any] | None = None) -> str:
        return value


window = _Window()
performance = _Performance()
localStorage = _LocalStorage()
caches = _Caches()
