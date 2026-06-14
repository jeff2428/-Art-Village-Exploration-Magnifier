from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path

LOADER_HTML = """
<div id="explorer-loader" role="status" aria-live="polite">
  <div class="explorer-scanner">
    <div class="explorer-lens">🔍</div>
    <div class="explorer-scanline"></div>
  </div>
  <div class="explorer-text">探險家載入中...</div>
  <div class="explorer-progress-track">
    <div class="explorer-progress-fill"></div>
  </div>
</div>
<style>
  #explorer-loader {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
    min-height: 100vh;
    background: linear-gradient(150deg, #e8f6f5 0%, #eef6df 50%, #f6ecdf 100%);
    color: #3d2a21;
    font-family: system-ui, "Microsoft JhengHei", sans-serif;
    text-align: center;
  }
  .explorer-scanner {
    position: relative;
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .explorer-lens {
    font-size: clamp(4rem, 18vw, 6rem);
    animation: explorer-scan 1.6s ease-in-out infinite;
    filter: drop-shadow(0 12px 20px rgba(61, 42, 33, 0.24));
    position: relative;
    z-index: 2;
  }
  .explorer-scanline {
    position: absolute;
    top: 0;
    left: -40%;
    width: 40%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(138, 90, 34, 0.15), transparent);
    border-radius: 50%;
    animation: explorer-sweep 1.6s ease-in-out infinite;
    z-index: 1;
  }
  .explorer-text {
    font-size: clamp(1.1rem, 4vw, 1.45rem);
    font-weight: 800;
    letter-spacing: 0.02em;
    animation: explorer-fade 2s ease-in-out infinite;
  }
  .explorer-progress-track {
    width: min(200px, 60vw);
    height: 4px;
    border-radius: 4px;
    background: rgba(61, 42, 33, 0.1);
    overflow: hidden;
  }
  .explorer-progress-fill {
    height: 100%;
    width: 30%;
    border-radius: 4px;
    background: linear-gradient(90deg, #8a5a22, #2f7d51, #8a5a22);
    background-size: 200% 100%;
    animation: explorer-progress 1.8s ease-in-out infinite;
  }
  @keyframes explorer-scan {
    0%, 100% { transform: translateX(-12px) rotate(-8deg) scale(0.95); }
    50% { transform: translateX(12px) rotate(8deg) scale(1.05); }
  }
  @keyframes explorer-sweep {
    0%, 100% { left: -40%; }
    50% { left: 100%; }
  }
  @keyframes explorer-fade {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }
  @keyframes explorer-progress {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
  }
</style>
<script>
  try {
    performance.mark("art-village:loader-start");
  } catch {}

  window.__artVillageReady = false;
  const artVillageBuildId = "__ART_VILLAGE_BUILD_ID__";
  const ANIMALS_WORKER_URL = "https://art-village-magnifier.jeff2428.workers.dev";

  const shouldRefreshRuntimeCache = () => {
    try {
      return localStorage.getItem("artVillageBuildId") !== artVillageBuildId;
    } catch {
      return true;
    }
  };

  const rememberRuntimeCache = () => {
    try {
      localStorage.setItem("artVillageBuildId", artVillageBuildId);
    } catch {}
  };

  if (shouldRefreshRuntimeCache()) {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations()
        .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
        .catch(() => {});
    }
    if ("caches" in window) {
      caches.keys()
        .then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
        .catch(() => {});
    }
    rememberRuntimeCache();
  }

  const prefetchAnimals = async () => {
    try {
      const response = await fetch(`${ANIMALS_WORKER_URL}/animals`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const data = await response.json();
      if (data && Array.isArray(data.animals)) {
        localStorage.setItem("artVillageAnimals", JSON.stringify({ animals: data.animals }));
        localStorage.setItem("artVillageAnimalsRemoteSyncedAt", String(Date.now()));
      }
    } catch {}
  };
  prefetchAnimals();

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
      try {
        performance.mark("art-village:flet-ready");
        performance.measure("art-village:loader-duration", "art-village:loader-start", "art-village:flet-ready");
        const measure = performance.getEntriesByName("art-village:loader-duration")[0];
        if (measure) {
          console.log(`🔍 探險放大鏡載入完成：${measure.duration.toFixed(0)}ms`);
        }
      } catch {}
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
    if (text) text.textContent = "載入時間較久，正在準備探險工具...";
  }, 20000);
</script>
"""


def build_stamp() -> str:
    raw_stamp = os.environ.get("FLET_BUILD_ID") or os.environ.get("CF_PAGES_COMMIT_SHA")
    if raw_stamp:
        return "".join(char for char in raw_stamp if char.isalnum() or char in "-_.")[:64]
    return str(int(time.time()))


def versioned_app_package_url(index_path: Path, stamp: str) -> str:
    app_path = index_path.parent / "assets" / "app" / "app.zip"
    versioned_name = f"app-{stamp}.zip"
    versioned_path = app_path.with_name(versioned_name)
    if app_path.exists():
        shutil.copyfile(app_path, versioned_path)
    return f"assets/app/{versioned_name}"


def runtime_asset_url(path: str, stamp: str) -> str:
    return f"{path}?v={stamp}"


def resource_hints(app_package_url: str, stamp: str) -> str:
    return f"""
  <link rel="preload" href="{app_package_url}" as="fetch" crossorigin>
  <link rel="preload" href="{runtime_asset_url('pyodide/pyodide.js', stamp)}" as="script">
  <link rel="preload" href="{runtime_asset_url('canvaskit/canvaskit.js', stamp)}" as="script">
"""


def service_worker_registration_script() -> str:
    return """
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((reg) => console.log('🔍 Service Worker 已註冊:', reg.scope))
        .catch((err) => console.warn('🔍 Service Worker 註冊失敗:', err));
    });
  }
</script>
"""


def generate_service_worker(sw_path: Path, stamp: str) -> None:
    sw_content = f"""
const CACHE_VERSION = '{stamp}';
const CACHE_NAME = `art-village-${{CACHE_VERSION}}`;

const RUNTIME_ASSETS = [
  '/pyodide/pyodide.js',
  '/pyodide/pyodide.asm.wasm',
  '/pyodide/pyodide.asm.data',
  '/canvaskit/canvaskit.js',
  '/canvaskit/canvaskit.wasm',
  '/canvaskit/chromium/canvaskit.js',
  '/canvaskit/chromium/canvaskit.wasm',
];

self.addEventListener('install', (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {{
      console.log('[SW] 更新 runtime 資源快取');
      return Promise.all(
        RUNTIME_ASSETS.map((asset) => {{
          return fetch(asset, {{ cache: 'reload' }}).then((response) => {{
            if (response.ok) {{
              cache.put(asset, response.clone());
            }}
            return response;
          }});
        }})
      );
    }}).catch(err => console.warn('[SW] 快取失敗:', err))
  );
  self.skipWaiting();
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil(
    caches.keys().then((keys) => {{
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME)
            .map((key) => {{
              console.log('[SW] 清除舊快取:', key);
              return caches.delete(key);
            }})
      );
    }})
  );
  self.clients.claim();
}});

self.addEventListener('fetch', (event) => {{
  const url = new URL(event.request.url);

  if (url.pathname.includes('/pyodide/') || url.pathname.includes('/canvaskit/')) {{
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {{
        return fetch(event.request, {{ cache: 'reload' }}).then((fetchResponse) => {{
          cache.put(event.request, fetchResponse.clone());
          return fetchResponse;
        }}).catch(() => cache.match(event.request));
      }})
    );
    return;
  }}

  if (url.pathname.includes('/assets/app/app-')) {{
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {{
        return fetch(event.request, {{ cache: 'reload' }}).then((networkResponse) => {{
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        }}).catch(() => {{
          return cache.match(event.request).then((cachedResponse) => {{
            if (cachedResponse) return cachedResponse;
            return fetch(event.request).then((networkResponse) => {{
              cache.put(event.request, networkResponse.clone());
              return networkResponse;
            }});
          }});
        }});
      }})
    );
    return;
  }}

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
}});
"""
    sw_path.write_text(sw_content.strip(), encoding="utf-8")
    print(f"[SW] 已生成 Service Worker: {sw_path}")


def cache_busting_script(stamp: str, app_package_url: str) -> str:
    return f"""
<script id="flet-cache-buster">
  flet.appPackageUrl = "{app_package_url}";
  flet.noCdn = true;
  flet.webRenderer = "canvaskit";
  flet.canvasKitVariant = "full";
  flet.pyodideUrl = `${{flet.pyodideUrl}}?v={stamp}`;
  if (typeof flet.canvasKitUrl === "string") {{
    flet.canvasKitUrl = `${{flet.canvasKitUrl}}?v={stamp}`;
  }}
  if (typeof flet.canvaskitUrl === "string") {{
    flet.canvaskitUrl = `${{flet.canvaskitUrl}}?v={stamp}`;
  }}
</script>
"""


def patch_index(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")
    stamp = build_stamp()
    app_package_url = versioned_app_package_url(index_path, stamp)
    loader_html = LOADER_HTML.replace("__ART_VILLAGE_BUILD_ID__", stamp)
    if 'rel="preload"' not in html:
        html = html.replace("</head>", f"{resource_hints(app_package_url, stamp)}</head>", 1)
    else:
        html, app_preload_count = re.subn(
            r'rel="preload" href="assets/app/app-[^"]+\.zip"',
            f'rel="preload" href="{app_package_url}"',
            html,
            count=1,
        )
        if app_preload_count == 0:
            html = html.replace(
                "</head>",
                f'  <link rel="preload" href="{app_package_url}" as="fetch" crossorigin>\n</head>',
                1,
            )
        html = re.sub(
            r'href="pyodide/pyodide\.js(?:\?v=[^"]+)?"',
            f'href="{runtime_asset_url("pyodide/pyodide.js", stamp)}"',
            html,
            count=1,
        )
        html = re.sub(
            r'href="canvaskit/canvaskit\.js(?:\?v=[^"]+)?"',
            f'href="{runtime_asset_url("canvaskit/canvaskit.js", stamp)}"',
            html,
            count=1,
        )
    python_script = '<script src="python.js"></script>'
    cache_buster = cache_busting_script(stamp, app_package_url).strip()
    cache_buster_pattern = re.compile(
        r'\s*<script id="flet-cache-buster">.*?</script>\s*',
        re.DOTALL,
    )
    if "flet-cache-buster" in html:
        html = cache_buster_pattern.sub(f"\n{cache_buster}\n\n  ", html, count=1)
    else:
        html = html.replace(python_script, f"{cache_buster}\n\n  {python_script}", 1)
    if "explorer-loader" not in html:
        if "<body>" in html:
            html = html.replace("<body>", f"<body>\n{loader_html}", 1)
        else:
            html = html.replace("</head>", f"</head>\n<body>\n{loader_html}", 1)
    else:
        html = re.sub(
            r'\n?<div id="explorer-loader"[\s\S]*?</script>\n?',
            f"\n{loader_html}\n",
            html,
            count=1,
        )
    if "serviceWorker" not in html:
        html = html.replace("</body>", f"{service_worker_registration_script()}</body>", 1)
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


def resolve_sw_path(index_path: Path) -> Path:
    return index_path.parent / "sw.js"


def cache_bust_runtime_references(content: str, stamp: str) -> str:
    for asset in (
        "pyodide/pyodide.js",
        "pyodide/pyodide.asm.wasm",
        "pyodide/pyodide.asm.data",
        "canvaskit/canvaskit.js",
        "canvaskit/canvaskit.wasm",
        "canvaskit/chromium/canvaskit.js",
        "canvaskit/chromium/canvaskit.wasm",
    ):
        content = re.sub(
            rf"(?P<asset>/?{re.escape(asset)})(?:\?v=[A-Za-z0-9_.-]+)?",
            rf"\g<asset>?v={stamp}",
            content,
        )
    return content


def patch_flutter_bootstrap(index_path: Path, stamp: str) -> None:
    fb_path = index_path.parent / "flutter_bootstrap.js"
    if fb_path.exists():
        content = fb_path.read_text(encoding="utf-8")
        patched = cache_bust_runtime_references(content, stamp)
        patched = force_full_canvaskit_variant(patched)
        if "serviceWorkerSettings:" in content:
            patched = re.sub(r'serviceWorkerSettings:\s*\{[^}]+\},', '', patched)
        if patched != content:
            fb_path.write_text(patched, encoding="utf-8")
            print(f"Patched {fb_path.name} runtime URLs.")


def force_full_canvaskit_variant(content: str) -> str:
    if 'canvasKitVariant: flet.canvasKitVariant || "full"' in content:
        return content
    return content.replace(
        "    assetBase: flet.assetBase\n};",
        '    assetBase: flet.assetBase,\n    canvasKitVariant: flet.canvasKitVariant || "full"\n};',
        1,
    )


if __name__ == "__main__":
    index_path = resolve_index_path()
    stamp = build_stamp()
    patch_index(index_path)
    patch_flutter_bootstrap(index_path, stamp)
    sw_path = resolve_sw_path(index_path)
    generate_service_worker(sw_path, stamp)
