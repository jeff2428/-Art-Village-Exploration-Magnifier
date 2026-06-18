from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import websockets

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "flet_app" / "build" / "web"
OUT_DIR = Path(tempfile.gettempdir()) / "art-village-static-build-smoke"
LOADER_FAILURE_TEXT = "探險工具載入失敗"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_http(url: str, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(0.4)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


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


def normalize_cdp_websocket_url(websocket_url: str) -> str:
    parsed = urllib.parse.urlsplit(websocket_url)
    host = "127.0.0.1" if parsed.hostname in {"localhost", "::1"} else parsed.hostname
    if not host:
        return websocket_url
    netloc = host
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


class StaticServer:
    def __init__(self, port: int) -> None:
        self.port = port
        self.proc: subprocess.Popen | None = None

    def __enter__(self) -> str:
        script = (
            "import http.server, socketserver; "
            "handler = http.server.SimpleHTTPRequestHandler; "
            "handler.extensions_map.update({'.wasm': 'application/wasm', '.js': 'application/javascript'}); "
            f"socketserver.TCPServer.allow_reuse_address = True; "
            f"httpd = socketserver.TCPServer(('127.0.0.1', {self.port}), handler); "
            "httpd.serve_forever()"
        )
        self.proc = subprocess.Popen(
            ["python", "-c", script],
            cwd=BUILD_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        url = f"http://127.0.0.1:{self.port}/"
        wait_http(url)
        return url

    def __exit__(self, *_args: Any) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=5)


class CdpClient:
    def __init__(self, websocket_url: str) -> None:
        self.websocket_url = websocket_url
        self.next_id = 1
        self.pending: dict[int, asyncio.Future] = {}
        self.events: list[dict[str, Any]] = []
        self.session_id: str | None = None
        self.ws: Any = None
        self.reader_task: asyncio.Task | None = None

    async def __aenter__(self) -> CdpClient:
        self.ws = await websockets.connect(self.websocket_url, max_size=32 * 1024 * 1024)
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

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        message_id = self.next_id
        self.next_id += 1
        future = asyncio.get_running_loop().create_future()
        self.pending[message_id] = future
        message: dict[str, Any] = {"id": message_id, "method": method, "params": params or {}}
        active_session = session_id if session_id is not None else self.session_id
        if active_session:
            message["sessionId"] = active_session
        await self.ws.send(json.dumps(message))
        result = await asyncio.wait_for(future, timeout=25)
        if "error" in result:
            raise RuntimeError(f"{method} failed: {result['error']}")
        return result.get("result", {})

    async def eval(self, expression: str) -> Any:
        result = await self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        return result.get("result", {}).get("value")

    async def wait_for_ready(self, timeout: float = 75.0) -> dict[str, Any]:
        deadline = time.time() + timeout
        state: dict[str, Any] = {}
        while time.time() < deadline:
            state = await self.eval(
                """
                (() => ({
                  ready: window.__artVillageReady === true,
                  loader: Boolean(document.getElementById('explorer-loader')),
                  hasFlutterView: Boolean(document.querySelector('flt-glass-pane, flutter-view, canvas')),
                  text: (document.body && (document.body.innerText || document.body.textContent) || '').slice(0, 500)
                }))()
                """
            )
            if LOADER_FAILURE_TEXT in str(state.get("text", "")):
                raise RuntimeError(
                    "Flet loader reported startup failure: "
                    + json.dumps(
                        {
                            "state": state,
                            "console_messages": self.console_messages(),
                            "network_failures": self.network_failures(),
                        },
                        ensure_ascii=False,
                    )
                )
            if state.get("ready") is True:
                await asyncio.sleep(1)
                state = await self.eval(
                    """
                    (() => ({
                      ready: window.__artVillageReady === true,
                      loader: Boolean(document.getElementById('explorer-loader')),
                      hasFlutterView: Boolean(document.querySelector('flt-glass-pane, flutter-view, canvas')),
                      text: (document.body && (document.body.innerText || document.body.textContent) || '').slice(0, 500)
                    }))()
                    """
                )
                return state
            await asyncio.sleep(1)
        raise RuntimeError(
            "Timed out waiting for Flet readiness: "
            + json.dumps(
                {
                    "state": state,
                    "console_messages": self.console_messages(),
                    "network_failures": self.network_failures(),
                },
                ensure_ascii=False,
            )
        )

    def console_messages(self) -> list[str]:
        messages: list[str] = []
        for event in self.events:
            method = event.get("method")
            params = event.get("params", {})
            if method == "Runtime.exceptionThrown":
                messages.append(json.dumps(params.get("exceptionDetails", {}), ensure_ascii=False)[:700])
            if method in {"Log.entryAdded", "Runtime.consoleAPICalled"}:
                level = params.get("entry", params).get("level") or params.get("type")
                if level in {"error", "warning"}:
                    messages.append(json.dumps(params, ensure_ascii=False)[:700])
        return messages

    def network_failures(self) -> list[str]:
        failures: list[str] = []
        for event in self.events:
            method = event.get("method")
            params = event.get("params", {})
            if method == "Network.loadingFailed":
                failures.append(json.dumps(params, ensure_ascii=False)[:700])
            if method == "Network.responseReceived":
                response = params.get("response", {})
                status = response.get("status", 0)
                if status >= 400:
                    failures.append(json.dumps(response, ensure_ascii=False)[:700])
        return failures


async def run_smoke(chrome_path: Path, url: str, cdp_port: int, headless: bool = True) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile_dir = OUT_DIR / "chrome-profile"
    if profile_dir.exists():
        shutil.rmtree(profile_dir)

    chrome_args = [
        str(chrome_path),
        "--use-angle=swiftshader",
        "--use-gl=swiftshader",
        "--disable-gpu-sandbox",
        "--disable-dev-shm-usage",
        f"--remote-debugging-port={cdp_port}",
        "--remote-allow-origins=*",
        "--window-size=430,900",
        f"--user-data-dir={profile_dir}",
    ]
    if headless:
        chrome_args.append("--headless=new")
    chrome_args.append(url)

    chrome_log = OUT_DIR / "chrome.log"
    chrome_log_handle = chrome_log.open("w", encoding="utf-8")
    chrome_proc = subprocess.Popen(chrome_args, stdout=chrome_log_handle, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + 25
        targets: Any = None
        last_error: Exception | None = None
        while time.time() < deadline:
            if chrome_proc.poll() is not None:
                raise RuntimeError(
                    f"Chrome exited before CDP became ready. Log: {chrome_log.read_text(encoding='utf-8', errors='replace')}"
                )
            try:
                targets = read_json(f"http://127.0.0.1:{cdp_port}/json/list", timeout=2)
                break
            except Exception as error:
                last_error = error
                time.sleep(0.5)
        if targets is None:
            raise RuntimeError(
                f"Timed out waiting for Chrome CDP: {last_error}. Log: {chrome_log.read_text(encoding='utf-8', errors='replace')}"
            )
        page_target = next(target for target in targets if target.get("type") == "page")
        browser_ws = normalize_cdp_websocket_url(read_json(f"http://127.0.0.1:{cdp_port}/json/version")["webSocketDebuggerUrl"])
        async with CdpClient(browser_ws) as cdp:
            attach = await cdp.call(
                "Target.attachToTarget",
                {"targetId": page_target["id"], "flatten": True},
                session_id="",
            )
            cdp.session_id = attach["sessionId"]
            try:
                await cdp.call("Runtime.enable")
                await cdp.call("Log.enable")
                await cdp.call("Network.enable")
            except TimeoutError:
                pass
            state = await cdp.wait_for_ready()
            messages = cdp.console_messages()
            link_errors = [message for message in messages if "LinkError" in message]
            if state.get("loader"):
                raise RuntimeError(f"Loader still visible after readiness: {state}")
            if link_errors:
                raise RuntimeError("Console contains LinkError: " + link_errors[0])
            return {"status": "passed", "state": state, "console_messages": messages}
    finally:
        if chrome_proc.poll() is None:
            chrome_proc.kill()
            try:
                chrome_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        chrome_log_handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    if not (BUILD_DIR / "index.html").exists():
        raise FileNotFoundError(f"Missing static build output: {BUILD_DIR}")
    server_port = free_port()
    cdp_port = free_port()
    with StaticServer(server_port) as url:
        result = asyncio.run(run_smoke(Path(args.chrome), url, cdp_port, headless=not args.headed))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
