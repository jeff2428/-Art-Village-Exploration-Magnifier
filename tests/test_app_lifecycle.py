"""Tests for app_lifecycle service."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "flet_app"))


class AppLifecycleTest(unittest.TestCase):
    """Verify AppLifecycle state transitions."""

    def setUp(self) -> None:
        self.state = MagicMock()
        self.state.pokedex = {}
        self.state.is_dark_mode = False
        self.state.camera_ready = False
        self.state.camera = None
        self.state.background_tasks = set()
        self.state.current_mode = MagicMock()
        self.state.current_mode.value = "landing"

        self.page = MagicMock()
        self.gallery_service = MagicMock()
        self.camera = MagicMock()
        self.status_text = MagicMock()
        self.create_background_task = MagicMock(side_effect=self._close_background_task)

    def _close_background_task(self, task):
        close = getattr(task, "close", None)
        if callable(close):
            close()

    def test_initializes_with_all_dependencies(self):
        from services.app_lifecycle import AppLifecycle

        lifecycle = AppLifecycle(
            page=self.page,
            state=self.state,
            gallery_service=self.gallery_service,
            camera=self.camera,
            status_text=self.status_text,
            create_background_task=self.create_background_task,
        )

        self.assertIsNotNone(lifecycle)

    def test_toggle_dark_mode_flips_state(self):
        from services.app_lifecycle import AppLifecycle
        from ui_theme import apply_theme  # noqa: F401

        lifecycle = AppLifecycle(
            page=self.page,
            state=self.state,
            gallery_service=self.gallery_service,
            camera=self.camera,
            status_text=self.status_text,
            create_background_task=self.create_background_task,
        )

        lifecycle.toggle_dark_mode()
        self.assertTrue(self.state.is_dark_mode)

    def test_toggle_dark_mode_calls_save_preference(self):
        from services.app_lifecycle import AppLifecycle

        lifecycle = AppLifecycle(
            page=self.page,
            state=self.state,
            gallery_service=self.gallery_service,
            camera=self.camera,
            status_text=self.status_text,
            create_background_task=self.create_background_task,
        )

        lifecycle.toggle_dark_mode()

        # create_background_task should have been called with save_dark_mode_preference coroutine
        call_args = self.create_background_task.call_args
        self.assertIsNotNone(call_args)

    def test_start_exploration_transitions_to_plant_mode(self):
        from app_types import AppMode
        from services.app_lifecycle import AppLifecycle

        self.page.scroll_to = AsyncMock()
        shell = MagicMock()
        welcome_screen = MagicMock()
        start_button = MagicMock()
        camera_manager = MagicMock()
        camera_manager.initialize = AsyncMock()

        lifecycle = AppLifecycle(
            page=self.page,
            state=self.state,
            gallery_service=self.gallery_service,
            camera=self.camera,
            status_text=self.status_text,
            create_background_task=self.create_background_task,
        )
        lifecycle._show_error_page = MagicMock()

        with (
            patch("services.app_lifecycle.ft.ProgressRing", return_value=MagicMock()),
            patch("services.app_lifecycle.ft.TextButton", return_value=MagicMock()),
            patch("services.app_lifecycle.ft.SegmentedButton", return_value=MagicMock()),
            patch("views.plant_view._build_plant_view", return_value=MagicMock()),
        ):
            asyncio.run(
                lifecycle.start_exploration(
                    shell,
                    welcome_screen,
                    start_button,
                    camera_manager,
                )
            )

        self.assertEqual(start_button.text, "準備中...")
        self.assertTrue(start_button.disabled)
        self.assertEqual(self.state.current_mode, AppMode.PLANT)
        self.assertTrue(shell.visible)
        self.assertFalse(welcome_screen.visible)
        lifecycle._show_error_page.assert_not_called()
        self.create_background_task.assert_called_once()


if __name__ == "__main__":
    unittest.main()
