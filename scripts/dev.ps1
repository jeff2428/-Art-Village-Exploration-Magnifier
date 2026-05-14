Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..\flet_app")

Write-Host "Starting Flet local development server..."
Write-Host "Keep this window open. Press Ctrl+C to stop."

flet run -d chrome
