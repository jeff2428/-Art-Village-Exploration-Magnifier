#!/usr/bin/env bash
set -euo pipefail

export FLET_CLI_NO_RICH_OUTPUT=1

echo "Installing Flet dependencies..." >&2
python -m pip install --upgrade pip
python -m pip install -r flet_app/requirements.txt

if [ -n "${WORKER_URL:-}" ]; then
  echo "Writing Cloudflare Worker URL into Flet build config..." >&2
  python -c "from pathlib import Path; import os; Path('flet_app/build_config.py').write_text('WORKER_URL = ' + repr(os.environ['WORKER_URL']) + '\n', encoding='utf-8')"
fi

echo "Building Flet web app for Cloudflare Pages..." >&2
cd flet_app
python -m flet build web --yes --verbose --route-url-strategy hash --web-renderer html
cd ..

echo "Patching loading screen..." >&2
python scripts/patch_flet_loader.py
