"""Logging configuration for Art Village Exploration Magnifier."""

from __future__ import annotations

import logging
import os


def setup_logging(level: int | None = None) -> None:
    """Configure root logger with sensible defaults.

    Environment variables:
        AV_LOG_LEVEL — one of DEBUG, INFO, WARNING, ERROR (default: WARNING in prod, DEBUG in dev)
    """
    if level is None:
        env_level = os.getenv("AV_LOG_LEVEL", "WARNING").upper()
        level = getattr(logging, env_level, logging.WARNING)

    # Only configure once
    if logging.getLogger().handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


# Convenience alias for the most common call site.
setup_logging()
