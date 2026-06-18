$ErrorActionPreference = "Stop"
$env:FLET_CLI_NO_RICH_OUTPUT = "1"
$env:PYTHONIOENCODING = "utf-8"

function Test-PythonModule {
    param(
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$ModuleName
    )
    & $PythonPath -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

$PythonCandidates = @(
    (Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"),
    (Join-Path $env:USERPROFILE "anaconda3\python.exe"),
    "python"
)
$Python = $null
foreach ($Candidate in $PythonCandidates) {
    $Resolved = $Candidate
    if (Test-Path $Candidate) {
        $Resolved = (Resolve-Path $Candidate).Path
    }
    if (Get-Command $Resolved -ErrorAction SilentlyContinue) {
        if (Test-PythonModule $Resolved "pip") {
            $Python = $Resolved
            break
        }
    }
}
if (-not $Python) {
    throw "Could not find a Python interpreter with pip."
}

$Flet = "flet"
$PythonScripts = Join-Path (Split-Path $Python -Parent) "flet.exe"
if (Test-Path $PythonScripts) {
    $Flet = (Resolve-Path $PythonScripts).Path
}

function Remove-Tree {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) {
        return
    }
    Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $_.Attributes = $_.Attributes -band (-bnot [System.IO.FileAttributes]::ReadOnly)
        } catch {}
    }
    Remove-Item -LiteralPath $Path -Recurse -Force
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
Invoke-Native $Python -m pip install --upgrade pip
Invoke-Native $Python -m pip install -r flet_app/requirements.txt
Invoke-Native $Python -m pip install "flet-cli==0.85.1"

Write-Host "Running Ruff linter..." -ForegroundColor Cyan
if (Test-PythonModule $Python "ruff") {
    Invoke-Native $Python -m ruff check flet_app/ tests/
} else {
    Write-Host "  ruff not found, skipping lint" -ForegroundColor Yellow
}

if ($env:WORKER_URL) {
    Write-Host "Writing Cloudflare Worker URL into Flet build config..." -ForegroundColor Cyan
    Invoke-Native $Python -c "from pathlib import Path; import os; Path('flet_app/build_config.py').write_text('WORKER_URL = ' + repr(os.environ['WORKER_URL']) + '\n', encoding='utf-8')"
}

Write-Host "Cleaning up any stale build directory..." -ForegroundColor Cyan
Remove-Tree "flet_app/build"

Write-Host "Building Flet web app for Cloudflare Pages..." -ForegroundColor Cyan
Set-Location "flet_app"
# We run flet build web
& $Flet build web --yes --verbose --route-url-strategy hash --web-renderer skwasm
if ($LASTEXITCODE -ne 0) {
    throw "Flet build failed with exit code ${LASTEXITCODE}."
}
Set-Location ".."

Write-Host "Validating Flet runtime metadata..." -ForegroundColor Cyan
Invoke-Native $Python scripts/validate_flet_runtime.py

Write-Host "Patching Flet app package with local modules..." -ForegroundColor Cyan
Invoke-Native $Python scripts/patch_flet_app_package.py

Write-Host "Patching loading screen..." -ForegroundColor Cyan
Invoke-Native $Python scripts/patch_flet_loader.py

Write-Host "Copying animal management page..." -ForegroundColor Cyan
if (Test-Path "flet_app/build/web/admin") {
    Remove-Tree "flet_app/build/web/admin"
}
Copy-Item -Recurse -Force "admin" "flet_app/build/web/admin"

Write-Host "Writing Cloudflare Pages cache headers..." -ForegroundColor Cyan
$WorkerUrl = if ($env:WORKER_URL) { $env:WORKER_URL } else { "https://art-village-magnifier.jeff2428.workers.dev" }
$HeadersContent = @"
/
  Cache-Control: no-store
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy-Report-Only: default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' $WorkerUrl https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval'; worker-src 'self' blob:; font-src 'self' data:; report-uri /__csp_report
  Report-To: {"group":"csp-endpoint","max_age":10886400,"endpoints":[{"url":"/__csp_report"}]}
/index.html
  Cache-Control: no-store
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: cross-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy-Report-Only: default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' $WorkerUrl https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval'; worker-src 'self' blob:; font-src 'self' data:; report-uri /__csp_report
  Report-To: {"group":"csp-endpoint","max_age":10886400,"endpoints":[{"url":"/__csp_report"}]}
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
"@
Set-Content -LiteralPath "flet_app/build/web/_headers" -Value $HeadersContent -Encoding utf8

Write-Host "Build complete! Output directory: flet_app/build/web" -ForegroundColor Green
