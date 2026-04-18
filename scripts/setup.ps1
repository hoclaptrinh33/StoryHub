$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    Set-Location $root
    python -m venv .venv
}

$python = Join-Path $root ".venv/Scripts/python.exe"

Write-Host "[StoryHub] Cai dependency backend..."
Set-Location (Join-Path $root "backend")
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Khong the cap nhat pip trong moi truong Python."
}

& $python -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    throw "Khong the cai dependency backend."
}

if ((Test-Path ".env.example") -and (-not (Test-Path ".env"))) {
    Copy-Item ".env.example" ".env"
}

Write-Host "[StoryHub] Khoi tao schema backend..."
& $python scripts/migrate.py up
if ($LASTEXITCODE -ne 0) {
    throw "Khong the khoi tao schema backend bang migration."
}

Write-Host "[StoryHub] Seed du lieu mau backend..."
& $python scripts/seed.py
if ($LASTEXITCODE -ne 0) {
    throw "Khong the seed du lieu mau backend."
}

Write-Host "[StoryHub] Cai dependency frontend..."
Set-Location (Join-Path $root "frontend")
npm install
if ($LASTEXITCODE -ne 0) {
    throw "Khong the cai dependency frontend."
}

if ((Test-Path ".env.example") -and (-not (Test-Path ".env"))) {
    Copy-Item ".env.example" ".env"
}

Write-Host "[StoryHub] Hoan tat setup moi truong."
