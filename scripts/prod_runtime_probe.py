from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image

from ui_smoke_cdp import CdpClient, read_json


OUT_DIR = Path(tempfile.gettempdir()) / "art-village-prod-probe"


def wait_for_targets(port: int, proc: subprocess.Popen, timeout: float = 25.0) -> list[dict[str, Any]]:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("Chrome exited before CDP became ready")
        try:
            return read_json(f"http://127.0.0.1:{port}/json/list")
        except (OSError, urllib.error.URLError, RuntimeError) as error:
            last_error = error
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for Chrome CDP: {last_error}")


def image_stats(path: Path) -> dict[str, Any]:
    image = Image.open(path).convert("RGB")
    sample = image.resize((86, 180))
    average = sample.resize((1, 1)).getpixel((0, 0))
    varied = 0
    dark = 0
    total = 0
    for red, green, blue in sample.getdata():
        total += 1
        if sum(abs(channel - average[index]) for index, channel in enumerate((red, green, blue))) > 18:
            varied += 1
        if red < 35 and green < 40 and blue < 45:
            dark += 1
    return {
        "size": image.size,
        "average": average,
        "variedRatio": round(varied / total, 4) if total else 0,
        "darkRatio": round(dark / total, 4) if total else 0,
    }


async def probe(chrome: Path, url: str, port: int, wait_seconds: float) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = OUT_DIR / f"profile-{int(time.time() * 1000)}"

    chrome_log = OUT_DIR / "chrome.log"
    with chrome_log.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [
                str(chrome),
                "--headless=new",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--remote-allow-origins=*",
                f"--remote-debugging-port={port}",
                "--window-size=430,900",
                f"--user-data-dir={profile}",
                url,
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            targets = wait_for_targets(port, proc)
            page_target = next(target for target in targets if target.get("type") == "page")
            websocket_url = page_target["webSocketDebuggerUrl"].replace("localhost", "127.0.0.1")
            async with CdpClient(websocket_url) as cdp:
                await cdp.call("Page.enable")
                await cdp.call("Runtime.enable")
                await cdp.call("Log.enable")
                await cdp.call("Network.enable")
                await asyncio.sleep(wait_seconds)
                state = await cdp.eval(
                    """
                    (() => ({
                      ready: window.__artVillageReady === true,
                      loader: Boolean(document.getElementById('explorer-loader')),
                      loaderText: (document.querySelector('#explorer-loader')?.innerText || '').slice(0, 500),
                      hasFlutterView: Boolean(document.querySelector('flt-glass-pane, flutter-view, canvas')),
                      canvasCount: document.querySelectorAll('canvas').length,
                      flutterViewCount: document.querySelectorAll('flt-glass-pane, flutter-view').length,
                      bodyText: (document.body?.innerText || document.body?.textContent || '').slice(0, 1000),
                      activeElement: document.activeElement?.tagName || null,
                      location: location.href
                    }))()
                    """
                )
                resources = await cdp.eval(
                    """
                    (() => performance.getEntriesByType('resource')
                      .map((entry) => ({
                        name: entry.name,
                        initiatorType: entry.initiatorType,
                        duration: Math.round(entry.duration),
                        transferSize: entry.transferSize || 0
                      }))
                      .filter((entry) => /python|pyodide|app-|main\\.dart|wasm|skwasm|flutter|canvaskit/.test(entry.name))
                    )()
                    """
                )
                console_events = []
                for event in cdp.events:
                    if event.get("method") == "Runtime.consoleAPICalled":
                        params = event.get("params", {})
                        args = []
                        for arg in params.get("args", []):
                            args.append(arg.get("value", arg.get("description", "")))
                        console_events.append({"type": params.get("type"), "args": args})
                screenshot = await cdp.screenshot("production")
                return {
                    "state": state,
                    "screenshot": str(screenshot),
                    "image": image_stats(screenshot),
                    "resources": resources,
                    "consoleAll": console_events[-80:],
                    "console": cdp.console_errors(),
                    "network": cdp.network_failures(),
                }
        finally:
            if proc.poll() is None:
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    parser.add_argument("--port", type=int, default=9337)
    parser.add_argument("--wait", type=float, default=45.0)
    args = parser.parse_args()
    result = asyncio.run(probe(Path(args.chrome), args.url, args.port, args.wait))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
