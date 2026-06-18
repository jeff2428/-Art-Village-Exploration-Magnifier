"""Shared error classes for Art Village Exploration Magnifier."""

from __future__ import annotations


class AppError(Exception):
    """Base application error with retryable flag."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class RecognitionError(AppError):
    """Errors from plant/animal recognition service."""

    pass


class CameraError(AppError):
    """Errors from camera initialization or capture."""

    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message, retryable=retryable)


class StorageError(AppError):
    """Errors from pokedex storage operations."""

    pass


def worker_error_message(status_code: int, text: str) -> str:
    """Map HTTP status codes to user-friendly messages in Traditional Chinese."""
    snippet = " ".join((text or "").strip().split())[:120]

    if status_code == 404 and "1042" in snippet:
        return "辨識服務尚未部署，請檢查 Worker 網址"
    if status_code in (400, 404):
        return "沒有辨識到植物，請對準葉子、花或果實再拍一次"
    if status_code == 405:
        return "辨識服務方法錯誤，請稍後再試"
    if status_code in (401, 403):
        return "辨識服務金鑰未通過，請檢查 Worker 的 PLANTNET_API_KEY"
    if status_code == 413:
        return "照片太大，請靠近植物後再拍一次"
    if status_code == 426:
        return "前端版本過舊，請稍後再拍一次"
    if status_code == 429:
        return "辨識服務忙碌，請稍後再試"
    if 500 <= status_code < 600:
        return "辨識服務暫時忙碌，請稍後再試"
    return f"辨識服務暫時無法處理（{status_code}）"
