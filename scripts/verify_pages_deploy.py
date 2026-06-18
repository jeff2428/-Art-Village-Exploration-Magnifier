from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://art-village-exploration-magnifier.pages.dev/"
PYODIDE_CDN_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js"
SKWASM_MISMATCH = "HTML forces skwasm but flutter_bootstrap.js has no valid skwasm build"


def read_url(url: str) -> tuple[str, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "art-village-deploy-verifier/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        body = response.read().decode("utf-8", errors="replace")
        return body, {key.lower(): value for key, value in response.headers.items()}


def fail_if(condition: bool, message: str, failures: list[str]) -> None:
    if condition:
        failures.append(message)


def extract_flutter_build_config(bootstrap: str) -> dict | None:
    match = re.search(r"_flutter\.buildConfig\s*=\s*(\{.*?\});", bootstrap, re.DOTALL)
    if match is None:
        return None
    try:
        parsed = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def has_valid_renderer_build(bootstrap: str, renderer: str) -> bool:
    build_config = extract_flutter_build_config(bootstrap)
    builds = build_config.get("builds") if build_config else None
    if not isinstance(builds, list):
        return False
    for build in builds:
        if (
            isinstance(build, dict)
            and build.get("renderer") == renderer
            and len(build) > 1
        ):
            return True
    return False


def verify_bootstrap(html: str, bootstrap: str, failures: list[str]) -> None:
    fail_if(extract_flutter_build_config(bootstrap) is None, "flutter_bootstrap.js build config missing or invalid", failures)
    if 'flet.webRenderer = "skwasm"' in html or 'webRenderer: "skwasm"' in html:
        fail_if(not has_valid_renderer_build(bootstrap, "skwasm"), SKWASM_MISMATCH, failures)


def verify_html(html: str, headers: dict[str, str], failures: list[str]) -> None:
    cache_buster_pos = html.find('id="flet-cache-buster"')
    python_pos = html.find('src="python.js"')
    link_header = headers.get("link", "")

    fail_if('flet.webRenderer = "skwasm"' not in html, 'missing skwasm cache-buster override', failures)
    fail_if('flet.webRenderer = "canvaskit"' in html, 'cache-buster still forces canvaskit', failures)
    fail_if('webRenderer: "canvaskit"' in html, 'initial Flet config still advertises canvaskit', failures)
    fail_if(cache_buster_pos < 0 or python_pos < 0 or cache_buster_pos > python_pos, 'cache-buster must run before python.js', failures)

    fail_if(PYODIDE_CDN_URL not in html, 'missing CDN Pyodide URL', failures)
    fail_if('pyodide/pyodide.js?v=' in html, 'local Pyodide preload is still versioned', failures)
    fail_if('canvaskit/canvaskit.js' in html, 'CanvasKit preload still present in HTML', failures)
    fail_if('canvaskit' in link_header.lower(), 'CanvasKit preload still present in Link header', failures)

    fail_if('<picture id="splash"' in html, 'Flet splash picture still present', failures)
    fail_if('id="splash-screen-style"' in html, 'Flet splash style still present', failures)
    fail_if('id="splash-screen-script"' in html, 'Flet splash script still present', failures)
    fail_if('id="splash-branding"' in html, 'Flet splash branding still present', failures)

    fail_if('id="explorer-loader"' not in html, 'custom explorer loader missing', failures)
    fail_if('removeFletSplash' not in html, 'runtime Flet splash cleanup missing', failures)
    fail_if('retryExplorerLoad' not in html, 'loader retry handler missing', failures)
    fail_if('window.addEventListener("error"' not in html, 'loader window error listener missing', failures)
    fail_if('window.addEventListener("unhandledrejection"' not in html, 'loader unhandled rejection listener missing', failures)

    app_match = re.search(r'flet\.appPackageUrl = "([^"]+app-[^"]+\.zip)"', html)
    fail_if(app_match is None, 'versioned app package URL missing', failures)
    fail_if('flet.appPackageUrl = "assets/app/app.zip"' in html, 'unversioned app package is still active', failures)


def verify_sw(sw: str, failures: list[str]) -> None:
    fail_if("/pyodide/pyodide.js" in sw, "service worker still caches local Pyodide", failures)
    fail_if("/pyodide/pyodide.asm.wasm" in sw, "service worker still caches local Pyodide wasm", failures)
    fail_if("url.pathname.includes('/pyodide/')" in sw, "service worker still intercepts local Pyodide", failures)
    fail_if("/canvaskit/canvaskit.js" in sw, "service worker still caches CanvasKit", failures)
    fail_if("url.pathname.includes('/canvaskit/')" in sw, "service worker still intercepts CanvasKit", failures)
    fail_if("/assets/app/app-" not in sw, "service worker no longer handles versioned app package", failures)


def verify(base_url: str) -> list[str]:
    normalized_base = base_url.rstrip("/") + "/"
    html, html_headers = read_url(normalized_base)
    sw, _sw_headers = read_url(urllib.parse.urljoin(normalized_base, "sw.js"))
    bootstrap, _bootstrap_headers = read_url(urllib.parse.urljoin(normalized_base, "flutter_bootstrap.js"))

    failures: list[str] = []
    verify_html(html, html_headers, failures)
    verify_sw(sw, failures)
    verify_bootstrap(html, bootstrap, failures)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify deployed Art Village Pages runtime artifacts.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    try:
        failures = verify(args.base_url)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"Deployment verification failed: could not fetch deployed site: {error}", file=sys.stderr)
        return 2

    if failures:
        print("Deployment verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Deployment verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
