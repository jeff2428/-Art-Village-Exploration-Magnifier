from __future__ import annotations

import os
import time
from pathlib import Path


LOADER_HTML = """
<div id="explorer-loader" role="status" aria-live="polite">
  <div class="explorer-lens">🔍</div>
  <div class="explorer-text">探險家載入中...</div>
</div>
<style>
  #explorer-loader {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: grid;
    place-content: center;
    gap: 1rem;
    min-height: 100vh;
    background: linear-gradient(135deg, #e8f6f5, #eef6df);
    color: #3d2a21;
    font-family: system-ui, "Microsoft JhengHei", sans-serif;
    text-align: center;
  }
  .explorer-lens {
    font-size: clamp(4rem, 18vw, 7rem);
    animation: explorer-pulse 1.15s ease-in-out infinite;
    filter: drop-shadow(0 12px 20px rgba(61, 42, 33, 0.24));
  }
  .explorer-text {
    font-size: clamp(1.1rem, 4vw, 1.45rem);
    font-weight: 800;
    letter-spacing: 0;
  }
  @keyframes explorer-pulse {
    0%, 100% { opacity: 0.46; transform: scale(0.94) rotate(-7deg); }
    50% { opacity: 1; transform: scale(1.06) rotate(5deg); }
  }
</style>
<script>
  window.__artVillageReady = false;

  const removeExplorerLoader = () => {
    const loader = document.getElementById("explorer-loader");
    if (loader) loader.remove();
  };

  const hasFletContent = () => {
    const flutterView = document.querySelector("flt-glass-pane, flutter-view, canvas");
    return Boolean(flutterView && flutterView.getBoundingClientRect().height > 20);
  };

  const waitForFlet = window.setInterval(() => {
    if (window.__artVillageReady === true) {
      window.clearInterval(waitForFlet);
      window.setTimeout(removeExplorerLoader, 450);
    }
  }, 250);

  window.setTimeout(() => {
    if (hasFletContent()) {
      removeExplorerLoader();
    }
  }, 45000);

  window.setTimeout(() => {
    const text = document.querySelector("#explorer-loader .explorer-text");
    if (text) text.textContent = "載入時間較久，請稍候或重新整理頁面";
  }, 20000);
</script>
"""


def build_stamp() -> str:
    raw_stamp = os.environ.get("FLET_BUILD_ID") or os.environ.get("CF_PAGES_COMMIT_SHA")
    if raw_stamp:
        return "".join(char for char in raw_stamp if char.isalnum() or char in "-_.")[:64]
    return str(int(time.time()))


def cache_busting_script(stamp: str) -> str:
    return f"""
<script id="flet-cache-buster">
  flet.appPackageUrl = `${{flet.appPackageUrl}}?v={stamp}`;
  flet.pyodideUrl = `${{flet.pyodideUrl}}?v={stamp}`;
</script>
"""


def patch_index(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")
    if "flet-cache-buster" not in html:
        html = html.replace('<script src="python.js"></script>', f'{cache_busting_script(build_stamp())}\n  <script src="python.js"></script>', 1)
    if "explorer-loader" in html:
        index_path.write_text(html, encoding="utf-8")
        return
    if "<body>" in html:
        html = html.replace("<body>", f"<body>\n{LOADER_HTML}", 1)
    else:
        html = html.replace("</head>", f"</head>\n<body>\n{LOADER_HTML}", 1)
    index_path.write_text(html, encoding="utf-8")


def resolve_index_path() -> Path:
    candidates = (
        Path("build/web/index.html"),
        Path("flet_app/build/web/index.html"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find Flet index.html. Run `flet build web` before patching."
    )


if __name__ == "__main__":
    patch_index(resolve_index_path())
