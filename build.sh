#!/usr/bin/env bash
set -euo pipefail

echo "Building Vite React web app for Cloudflare Pages..." >&2
cd flet_app
# Clear node_modules to avoid caching issues with permissions on Cloudflare Pages
rm -rf node_modules package-lock.json
npm install
chmod +x node_modules/.bin/*
npm run build
cd ..

echo "Copying animal management page..." >&2
rm -rf flet_app/build/web/admin
cp -R admin flet_app/build/web/admin

echo "Writing Cloudflare Pages cache headers..." >&2
python -c "
from pathlib import Path
import os
worker_url = os.environ.get('WORKER_URL', 'https://art-village-magnifier.jeff2428.workers.dev')
headers_content = f'''/
  Cache-Control: no-cache, no-store, must-revalidate
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy-Report-Only: default-src '\''self'\''; img-src '\''self'\'' data: blob:; media-src '\''self'\'' blob:; connect-src '\''self'\'' {worker_url} https://cdn.jsdelivr.net; style-src '\''self'\'' '\''unsafe-inline'\''; script-src '\''self'\'' https://cdn.jsdelivr.net '\''unsafe-eval'\''; worker-src '\''self'\'' blob:; font-src '\''self'\'' data:; report-uri /__csp_report
/assets/*
  Cache-Control: public, max-age=31536000, immutable
'''
Path('flet_app/build/web/_headers').write_text(headers_content, encoding='utf-8')
"
