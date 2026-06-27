from __future__ import annotations

from typing import Any


class _Window:
    def __setattr__(self, _name: str, _value: Any) -> None:
        pass

    async def compressImageAsync(self, _src: str, _max_width: int, _quality: float) -> str:  # noqa: N802
        return ""


class _Performance:
    def mark(self, _name: str) -> None:
        return None


class _LocalStorage:
    def getItem(self, _key: str) -> None:  # noqa: N802
        return None

    def setItem(self, _key: str, _value: str) -> None:  # noqa: N802
        return None

    def removeItem(self, _key: str) -> None:  # noqa: N802
        return None


class _CacheResponse:
    async def text(self) -> str:
        return ""


class _Cache:
    async def match(self, _key: str) -> _CacheResponse | None:
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


class _Blob:
    @classmethod
    def new(cls, _parts: list[Any], _options: dict[str, Any] | None = None) -> _Blob:
        return cls()


class _FormData:
    @classmethod
    def new(cls) -> _FormData:
        return cls()

    def append(self, _name: str, _value: Any, _filename: str | None = None) -> None:
        return None


class _Object:
    @staticmethod
    def fromEntries(_value: Any) -> dict[str, Any]:  # noqa: N802
        return {}


class _Uint8Array:
    @classmethod
    def new(cls, _value: Any) -> _Uint8Array:
        return cls()


class _FetchResponse:
    ok = True
    status = 200

    async def text(self) -> str:
        return "{}"


async def evalJS(_source: str) -> Any:  # noqa: N802
    return None


def eval(_source: str) -> Any:  # noqa: A001
    return None


async def fetch(_url: str, _options: Any | None = None) -> _FetchResponse:
    return _FetchResponse()


window = _Window()
performance = _Performance()
localStorage = _LocalStorage()  # noqa: N816
caches = _Caches()
Blob = _Blob
FormData = _FormData
Object = _Object
Uint8Array = _Uint8Array
