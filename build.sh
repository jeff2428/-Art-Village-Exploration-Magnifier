#!/usr/bin/env bash
set -euo pipefail

export FLET_CLI_NO_RICH_OUTPUT=1
export FLET_BUILD_ID="${CF_PAGES_COMMIT_SHA:-$(date +%s)}"
export PYTHONIOENCODING=utf-8

if [ -f "docs/PRE_BUILD_NOTES.md" ]; then
  echo "Reading pre-build notes..." >&2
  python -c "from pathlib import Path; print('\n'.join(Path('docs/PRE_BUILD_NOTES.md').read_text(encoding='utf-8').splitlines()[:180]))" >&2
fi

echo "Installing dependencies..." >&2
python -m pip install --upgrade pip
python -m pip install -r flet_app/requirements.txt
python -m pip install "flet-cli==0.85.1"

if command -v ruff &> /dev/null; then
  echo "Running Ruff lint..." >&2
  python -m ruff check --target-version py312 flet_app/ tests/
fi

if [ -n "${WORKER_URL:-}" ]; then
  echo "Writing Cloudflare Worker URL into Flet build config..." >&2
  python -c "from pathlib import Path; import os; Path('flet_app/build_config.py').write_text('WORKER_URL = ' + repr(os.environ['WORKER_URL']) + '\n', encoding='utf-8')"
fi

echo "Cleaning up any stale build directory..." >&2
rm -rf flet_app/build

echo "Building Flet web app for Cloudflare Pages..." >&2
cd flet_app
flet build web --yes --verbose --route-url-strategy hash --web-renderer skwasm
cd ..

echo "Validating Flet runtime metadata..." >&2
python scripts/validate_flet_runtime.py

echo "Patching Flet app package with local modules..." >&2
python scripts/patch_flet_app_package.py

echo "Patching loading screen..." >&2
python scripts/patch_flet_loader.py

echo "Copying animal management page..." >&2
rm -rf flet_app/build/web/admin
cp -R admin flet_app/build/web/admin

echo "Writing Cloudflare Pages cache headers..." >&2
python -c "
from pathlib import Path
import os
worker_url = os.environ.get('WORKER_URL', 'https://art-village-magnifier.jeff2428.workers.dev')
headers_content = f'''/
  Cache-Control: no-store
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy-Report-Only: default-src '\''self'\''; img-src '\''self'\'' data: blob:; media-src '\''self'\'' blob:; connect-src '\''self'\'' {worker_url} https://cdn.jsdelivr.net; style-src '\''self'\'' '\''unsafe-inline'\''; script-src '\''self'\'' https://cdn.jsdelivr.net '\''wasm-unsafe-eval'\''; worker-src '\''self'\'' blob:; font-src '\''self'\'' data:; report-uri /__csp_report
  Report-To: {{\"group\":\"csp-endpoint\",\"max_age\":10886400,\"endpoints\":[{{\"url\":\"/__csp_report\"}]}}}
/index.html
  Cache-Control: no-store
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy-Report-Only: default-src '\''self'\''; img-src '\''self'\'' data: blob:; media-src '\''self'\'' blob:; connect-src '\''self'\'' {worker_url} https://cdn.jsdelivr.net; style-src '\''self'\'' '\''unsafe-inline'\''; script-src '\''self'\'' https://cdn.jsdelivr.net '\''wasm-unsafe-eval'\''; worker-src '\''self'\'' blob:; font-src '\''self'\'' data:; report-uri /__csp_report
  Report-To: {{\"group\":\"csp-endpoint\",\"max_age\":10886400,\"endpoints\":[{{\"url\":\"/__csp_report\"}]}}}
/flutter_service_worker.js
  Cache-Control: no-cache, no-store, must-revalidate
  X-Content-Type-Options: nosniff
/assets/app/app.zip
  Cache-Control: no-store
/assets/app/app-*.zip
  Cache-Control: public, max-age=31536000, immutable
/pyodide/*
  Cache-Control: no-cache, no-store, must-revalidate
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
/canvaskit/*
  Cache-Control: no-cache, no-store, must-revalidate
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
/*.js
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
/*.mjs
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
/*.wasm
  Cache-Control: no-cache, no-store, must-revalidate
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
/sw.js
  Cache-Control: no-cache, no-store, must-revalidate
  X-Content-Type-Options: nosniff
'''
Path('flet_app/build/web/_headers').write_text(headers_content, encoding='utf-8')
"
