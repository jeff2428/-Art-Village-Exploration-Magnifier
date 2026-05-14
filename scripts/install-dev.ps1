Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

Write-Host "Installing local Flet dependencies..."
python -m pip install --upgrade pip
python -m pip install -r flet_app/requirements.txt

Write-Host "Done. Start local development with:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/dev.ps1"
