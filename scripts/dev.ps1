Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$rootDir = Join-Path $PSScriptRoot ".."
Set-Location $rootDir

Write-Host "Running lint checks..." -ForegroundColor Cyan
if (Get-Command "ruff" -ErrorAction SilentlyContinue) {
    python -m ruff check flet_app/ tests/
} else {
    Write-Host "  ruff not found, skipping lint" -ForegroundColor Yellow
}

Write-Host "Starting Flet local development server..." -ForegroundColor Cyan
Write-Host "Keep this window open. Press Ctrl+C to stop." -ForegroundColor Yellow

Set-Location (Join-Path $rootDir "flet_app")
flet run -d -w main.py
