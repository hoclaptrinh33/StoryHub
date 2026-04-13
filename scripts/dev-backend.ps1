param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    throw "Khong tim thay .venv. Hay chay scripts/setup.ps1 truoc."
}

Set-Location (Join-Path $root "backend")

if ((Test-Path ".env.example") -and (-not (Test-Path ".env"))) {
    Copy-Item ".env.example" ".env"
}

& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
