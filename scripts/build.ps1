$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r flet_app/requirements.txt
python -m pip install "flet-cli==0.85.1"

Write-Host "Running Ruff linter..." -ForegroundColor Cyan
if (Get-Command "ruff" -ErrorAction SilentlyContinue) {
    python -m ruff check flet_app/ tests/
} else {
    Write-Host "  ruff not found, skipping lint" -ForegroundColor Yellow
}

if ($env:WORKER_URL) {
    Write-Host "Writing Cloudflare Worker URL into Flet build config..." -ForegroundColor Cyan
    python -c "from pathlib import Path; import os; Path('flet_app/build_config.py').write_text('WORKER_URL = ' + repr(os.environ['WORKER_URL']) + '\n', encoding='utf-8')"
}

Write-Host "Cleaning up any stale build directory..." -ForegroundColor Cyan
if (Test-Path "flet_app/build") {
    Remove-Item -Recurse -Force "flet_app/build"
}

Write-Host "Building Flet web app for Cloudflare Pages..." -ForegroundColor Cyan
Set-Location "flet_app"
# We run flet build web
flet build web --yes --verbose --route-url-strategy hash --web-renderer auto --no-wasm
Set-Location ".."

Write-Host "Patching Flet app package with local modules..." -ForegroundColor Cyan
python scripts/patch_flet_app_package.py

Write-Host "Patching loading screen..." -ForegroundColor Cyan
python scripts/patch_flet_loader.py

Write-Host "Copying animal management page..." -ForegroundColor Cyan
if (Test-Path "flet_app/build/web/admin") {
    Remove-Item -Recurse -Force "flet_app/build/web/admin"
}
Copy-Item -Recurse -Force "admin" "flet_app/build/web/admin"

Write-Host "Writing Cloudflare Pages cache headers..." -ForegroundColor Cyan
python -c "from pathlib import Path; Path('flet_app/build/web/_headers').write_text('''/index.html
  Cache-Control: no-store
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
/flutter_service_worker.js
  Cache-Control: no-cache, no-store, must-revalidate
/assets/app/app.zip
  Cache-Control: no-store
/assets/app/app-*.zip
  Cache-Control: public, max-age=31536000, immutable
/pyodide/*
  Cache-Control: public, max-age=31536000, immutable
/canvaskit/*
  Cache-Control: public, max-age=31536000, immutable
/*.wasm
  Cache-Control: public, max-age=31536000, immutable
/sw.js
  Cache-Control: no-cache, no-store, must-revalidate
''', encoding='utf-8')"

Write-Host "Build complete! Output directory: flet_app/build/web" -ForegroundColor Green
