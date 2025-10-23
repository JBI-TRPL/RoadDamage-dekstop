# Build script for Windows release
# Usage (PowerShell): .\build_release_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "🔨 Building VGTECH Road Damage Detector for Windows..." -ForegroundColor Cyan

# Read version
$VERSION = Get-Content VERSION
Write-Host "Version: $VERSION"

# Check if venv is active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not active. Activating..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Install PyInstaller if not present
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# Build executable
Write-Host "🚀 Building executable..." -ForegroundColor Green
pyinstaller build-windows.spec

# Create release directory
$RELEASE_DIR = "releases\vgtech-road-damage-detector-v$VERSION-windows"
New-Item -ItemType Directory -Force -Path $RELEASE_DIR | Out-Null

# Copy built files
Write-Host "📦 Packaging release..." -ForegroundColor Yellow
Copy-Item -Recurse "dist\road-damage-detector-windows\*" "$RELEASE_DIR\"
Copy-Item VERSION "$RELEASE_DIR\"
Copy-Item README.md "$RELEASE_DIR\"
Copy-Item CHANGELOG.md "$RELEASE_DIR\"
Copy-Item .env.example "$RELEASE_DIR\.env"
Copy-Item -Recurse models "$RELEASE_DIR\" -ErrorAction SilentlyContinue

# Create run script
$runScript = @'
@echo off
REM Run VGTECH Road Damage Detector

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env not found. Creating from template...
    copy .env.example .env
    echo Please edit .env and configure your settings:
    echo   - CAM0, CAM1 (camera indices, e.g., 0, 1)
    echo   - TFLITE_MODEL (model path)
    echo   - SUPABASE_URL, SUPABASE_ANON_KEY
    pause
    exit /b 1
)

REM Run application
road-damage-detector.exe
pause
'@

$runScript | Out-File -FilePath "$RELEASE_DIR\run.bat" -Encoding ASCII

# Create archive
Write-Host "📦 Creating archive..." -ForegroundColor Yellow
Compress-Archive -Path $RELEASE_DIR -DestinationPath "releases\vgtech-road-damage-detector-v$VERSION-windows-x64.zip" -Force

Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "Release: releases\vgtech-road-damage-detector-v$VERSION-windows-x64.zip"
Write-Host ""
Write-Host "To test:"
Write-Host "  cd releases\vgtech-road-damage-detector-v$VERSION-windows"
Write-Host "  .\run.bat"
