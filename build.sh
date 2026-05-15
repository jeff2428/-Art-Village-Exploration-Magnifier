#!/usr/bin/env bash
set -euo pipefail

export FLET_CLI_NO_RICH_OUTPUT=1
export FLET_BUILD_ID="${CF_PAGES_COMMIT_SHA:-$(date +%s)}"

if [ -f "docs/PRE_BUILD_NOTES.md" ]; then
  echo "Reading pre-build notes..." >&2
  python -c "from pathlib import Path; print('\n'.join(Path('docs/PRE_BUILD_NOTES.md').read_text(encoding='utf-8').splitlines()[:180]))" >&2
fi

echo "Installing Flet dependencies..." >&2
python -m pip install --upgrade pip
python -m pip install -r flet_app/requirements.txt

if [ -n "${WORKER_URL:-}" ]; then
  echo "Writing Cloudflare Worker URL into Flet build config..." >&2
  python -c "from pathlib import Path; import os; Path('flet_app/build_config.py').write_text('WORKER_URL = ' + repr(os.environ['WORKER_URL']) + '\n', encoding='utf-8')"
fi

echo "Building Flet web app for Cloudflare Pages..." >&2
cd flet_app
flet build web --yes --verbose --route-url-strategy hash --web-renderer auto
cd ..

echo "Patching loading screen..." >&2
python scripts/patch_flet_loader.py

echo "Writing Cloudflare Pages cache headers..." >&2
python -c "from pathlib import Path; Path('flet_app/build/web/_headers').write_text('''/index.html\n  Cache-Control: no-store\n/flutter_service_worker.js\n  Cache-Control: no-cache, no-store, must-revalidate\n/assets/app/app.zip\n  Cache-Control: no-store\n/assets/app/app-*.zip\n  Cache-Control: public, max-age=31536000, immutable\n/pyodide/*\n  Cache-Control: public, max-age=31536000, immutable\n/canvaskit/*\n  Cache-Control: public, max-age=31536000, immutable\n''', encoding='utf-8')"
