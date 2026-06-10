from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import websockets
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "flet_app"
OUT_DIR = Path(tempfile.gettempdir()) / "art-village-ui-smoke"
SMOKE_PORT = 8561


def wait_http(url: str, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.4)
    raise RuntimeError(f"Timed out waiting for {url}")


def read_json(url: str, timeout: float = 20.0) -> Any:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:
            last_error = error
            time.sleep(0.4)
    raise RuntimeError(f"Timed out reading {url}: {last_error}")


class CdpClient:
    def __init__(self, websocket_url: str) -> None:
        self.websocket_url = websocket_url
        self.next_id = 1
        self.pending: dict[int, asyncio.Future] = {}
        self.events: list[dict[str, Any]] = []
        self.ws: Any = None
        self.reader_task: asyncio.Task | None = None

    async def __aenter__(self) -> CdpClient:
        self.ws = await websockets.connect(self.websocket_url, max_size=16 * 1024 * 1024)
        self.reader_task = asyncio.create_task(self._reader())
        return self

    async def __aexit__(self, *_args: Any) -> None:
        if self.reader_task:
            self.reader_task.cancel()
        if self.ws:
            await self.ws.close()

    async def _reader(self) -> None:
        async for raw in self.ws:
            message = json.loads(raw)
            if "id" in message:
                future = self.pending.pop(message["id"], None)
                if future and not future.done():
                    future.set_result(message)
            else:
                self.events.append(message)

    async def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        future = asyncio.get_running_loop().create_future()
        self.pending[message_id] = future
        await self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        result = await asyncio.wait_for(future, timeout=20)
        if "error" in result:
            raise RuntimeError(f"{method} failed: {result['error']}")
        return result.get("result", {})

    async def eval(self, expression: str) -> Any:
        result = await self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        return result.get("result", {}).get("value")

    async def click_text(self, text: str) -> dict[str, Any]:
        rect = await self.eval(
            f"""
            (() => {{
              const target = {json.dumps(text)};
              const nodes = Array.from(document.querySelectorAll('*'));
              const candidates = nodes
                .filter((node) => (node.innerText || node.textContent || '').includes(target))
                .map((node) => {{
                  const rect = node.getBoundingClientRect();
                  return {{
                    x: rect.x, y: rect.y, width: rect.width, height: rect.height,
                    area: rect.width * rect.height,
                    text: (node.innerText || node.textContent || '').trim().slice(0, 80)
                  }};
                }})
                .filter((rect) => rect.width > 0 && rect.height > 0)
                .sort((a, b) => a.area - b.area);
              return candidates[0] || null;
            }})()
            """
        )
        if not rect:
            raise RuntimeError(f"Could not find visible text: {text}")
        x = rect["x"] + rect["width"] / 2
        y = rect["y"] + rect["height"] / 2
        await self.click_point(x, y)
        await asyncio.sleep(0.8)
        return rect

    async def click_point(self, x: float, y: float) -> None:
        point_x = round(x)
        point_y = round(y)
        await self.call(
            "Input.dispatchMouseEvent",
            {"type": "mouseMoved", "x": point_x, "y": point_y, "button": "none", "buttons": 0},
        )
        await self.call(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": point_x, "y": point_y, "button": "left", "buttons": 1, "clickCount": 1},
        )
        await self.call(
            "Input.dispatchMouseEvent",
            {"type": "mouseReleased", "x": point_x, "y": point_y, "button": "left", "buttons": 0, "clickCount": 1},
        )
        await self.call(
            "Input.dispatchTouchEvent",
            {"type": "touchStart", "touchPoints": [{"x": point_x, "y": point_y, "radiusX": 2, "radiusY": 2}]},
        )
        await self.call("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        await asyncio.sleep(0.8)

    async def click_text_or_point(self, text: str, x: float, y: float) -> str:
        try:
            await self.click_text(text)
            return f"text:{text}"
        except RuntimeError:
            await self.click_point(x, y)
            return f"point:{x:.0f},{y:.0f}"

    async def screenshot(self, name: str) -> Path:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        result = await self.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        path = OUT_DIR / f"{name}.png"
        path.write_bytes(base64.b64decode(result["data"]))
        return path

    def is_blank(self, path: Path) -> bool:
        image = Image.open(path).convert("RGB").resize((43, 90))
        average = image.resize((1, 1)).getpixel((0, 0))
        varied_pixels = 0
        for pixel in image.getdata():
            if sum(abs(pixel[index] - average[index]) for index in range(3)) > 18:
                varied_pixels += 1
        return varied_pixels < 12

    def has_dark_lens(self, path: Path) -> bool:
        image = Image.open(path).convert("RGB")
        width, height = image.size
        dark_pixels = 0
        sample_pixels = 0
        for y in range(round(height * 0.22), round(height * 0.72), 8):
            for x in range(round(width * 0.10), round(width * 0.90), 8):
                red, green, blue = image.getpixel((x, y))
                sample_pixels += 1
                if red < 45 and green < 60 and blue < 50:
                    dark_pixels += 1
        return sample_pixels > 0 and dark_pixels / sample_pixels > 0.12

    async def wait_for_nonblank_screenshot(self, name: str, timeout: float = 45.0) -> Path:
        deadline = time.time() + timeout
        last_path = OUT_DIR / f"{name}.png"
        while time.time() < deadline:
            last_path = await self.screenshot(name)
            if not self.is_blank(last_path):
                return last_path
            await asyncio.sleep(1)
        raise RuntimeError(f"{name} screenshot appears blank: {last_path}")

    async def wait_for_changed_screenshot(self, name: str, previous_path: Path, timeout: float = 12.0) -> Path:
        previous_hash = hashlib.sha256(previous_path.read_bytes()).hexdigest()
        deadline = time.time() + timeout
        last_path = OUT_DIR / f"{name}.png"
        while time.time() < deadline:
            last_path = await self.wait_for_nonblank_screenshot(name, timeout=3)
            current_hash = hashlib.sha256(last_path.read_bytes()).hexdigest()
            if current_hash != previous_hash:
                return last_path
            await asyncio.sleep(1)
        raise RuntimeError(f"{name} screenshot did not change after interaction: {last_path}")

    async def wait_for_main_screen(self, name: str, timeout: float = 20.0) -> Path:
        deadline = time.time() + timeout
        last_path = OUT_DIR / f"{name}.png"
        while time.time() < deadline:
            last_path = await self.wait_for_nonblank_screenshot(name, timeout=3)
            if self.has_dark_lens(last_path):
                return last_path
            await asyncio.sleep(1)
        raise RuntimeError(f"{name} did not reach the main magnifier screen: {last_path}")

    def console_errors(self) -> list[str]:
        messages: list[str] = []
        for event in self.events:
            method = event.get("method")
            params = event.get("params", {})
            if method == "Runtime.exceptionThrown":
                detail = params.get("exceptionDetails", {})
                messages.append(detail.get("text", "Runtime exception"))
            if method in {"Log.entryAdded", "Runtime.consoleAPICalled"}:
                level = params.get("entry", params).get("level") or params.get("type")
                if level in {"error", "warning"}:
                    messages.append(json.dumps(params, ensure_ascii=False)[:500])
        return messages


async def run_smoke(chrome_path: Path, headless: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile_dir = OUT_DIR / "chrome-profile"
    if profile_dir.exists():
        shutil.rmtree(profile_dir)

    flet_proc = subprocess.Popen(
        ["flet", "run", "-w", "-p", str(SMOKE_PORT), "--host", "127.0.0.1", "main.py"],
        cwd=APP_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    chrome_proc: subprocess.Popen | None = None
    result: dict[str, Any] | None = None
    try:
        app_url = f"http://127.0.0.1:{SMOKE_PORT}"
        wait_http(app_url)
        chrome_args = [
            str(chrome_path),
            "--disable-gpu",
            "--remote-debugging-port=9223",
            "--window-size=430,900",
            f"--user-data-dir={profile_dir}",
        ]
        if headless:
            chrome_args.append("--headless=new")
        chrome_args.append(app_url)
        chrome_proc = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        targets = read_json("http://127.0.0.1:9223/json/list")
        page_target = next(target for target in targets if target.get("type") == "page")
        async with CdpClient(page_target["webSocketDebuggerUrl"]) as cdp:
            await cdp.call("Page.enable")
            await cdp.call("Runtime.enable")
            await cdp.call("Log.enable")
            welcome_shot = await cdp.wait_for_nonblank_screenshot("01-welcome")
            screenshots = [str(welcome_shot)]
            actions = [await cdp.click_text_or_point("開始探險", 215, 650)]
            await asyncio.sleep(1)
            after_click_shot = await cdp.wait_for_changed_screenshot("02-after-click", welcome_shot)
            screenshots.append(str(after_click_shot))
            await asyncio.sleep(3)
            after_start_shot = await cdp.wait_for_main_screen("03-after-start")
            screenshots.append(str(after_start_shot))
            actions.append(await cdp.click_text_or_point("動物", 280, 138))
            screenshots.append(str(await cdp.screenshot("04-animal-mode")))
            actions.append(await cdp.click_text_or_point("植物", 198, 138))
            screenshots.append(str(await cdp.screenshot("05-plant-mode")))
            actions.append(await cdp.click_text_or_point("深色模式", 435, 42))
            screenshots.append(str(await cdp.screenshot("06-dark-mode")))
            body_text = await cdp.eval("document.body.innerText || document.body.textContent || ''")
            result = {
                "status": "passed",
                "actions": actions,
                "screenshots": screenshots,
                "console_errors": cdp.console_errors(),
                "observed_text": str(body_text)[:500],
            }
            return result
    finally:
        if chrome_proc and chrome_proc.poll() is None:
            chrome_proc.kill()
        if flet_proc.poll() is None:
            flet_proc.kill()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(run_smoke(Path(args.chrome), headless=not args.headed))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
