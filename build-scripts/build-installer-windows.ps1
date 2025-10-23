# Installer script for VGTECH Road Damage Detector (Windows)
# This script builds and packages the application as a standalone .exe

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
Set-Location $PROJECT_ROOT

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VGTECH Road Damage Detector - Windows Installer Builder" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Read version
if (-not (Test-Path VERSION)) {
    Write-Error "❌ VERSION file not found!"
    exit 1
}

$VERSION = Get-Content VERSION
Write-Host "📦 Building version: $VERSION" -ForegroundColor Green
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Python not found. Please install Python 3.8+"
    exit 1
}

$PYTHON_VERSION = (python --version) -replace "Python ", ""
Write-Host "✅ Python version: $PYTHON_VERSION" -ForegroundColor Green

# Check/create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip -q

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

# Install PyInstaller
Write-Host "📥 Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller -q

# Generate icon if it doesn't exist
if (-not (Test-Path "icon.ico")) {
    Write-Host "🎨 Generating application icon..." -ForegroundColor Yellow
    pip install Pillow -q
    python create_icon.py
}

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

# Build executable using spec file
Write-Host "🔨 Building standalone executable..." -ForegroundColor Green
if (Test-Path "build-windows.spec") {
    pyinstaller build-windows.spec --clean
} else {
    Write-Error "❌ build-windows.spec not found!"
    exit 1
}

# Create release directory
$RELEASE_NAME = "vgtech-road-damage-detector-v$VERSION-windows-x64"
$RELEASE_DIR = "releases\$RELEASE_NAME"
New-Item -ItemType Directory -Force -Path $RELEASE_DIR | Out-Null

Write-Host "📦 Packaging release..." -ForegroundColor Yellow

# Copy built files
Copy-Item -Recurse "dist\road-damage-detector-windows\*" "$RELEASE_DIR\"

# Copy documentation
Copy-Item VERSION "$RELEASE_DIR\"
Copy-Item README.md "$RELEASE_DIR\"
Copy-Item CHANGELOG.md "$RELEASE_DIR\"
Copy-Item QUICKSTART.md "$RELEASE_DIR\" -ErrorAction SilentlyContinue

# Copy example config
Copy-Item .env.example "$RELEASE_DIR\.env"

# Copy models if present
if (Test-Path "models") {
    New-Item -ItemType Directory -Force -Path "$RELEASE_DIR\models" | Out-Null
    Copy-Item "models\*.tflite" "$RELEASE_DIR\models\" -ErrorAction SilentlyContinue
}

# Create data directory
New-Item -ItemType Directory -Force -Path "$RELEASE_DIR\data" | Out-Null

# Create run script (batch file)
$runBatch = @'
@echo off
REM VGTECH Road Damage Detector Launcher

echo ================================
echo VGTECH Road Damage Detector
echo ================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] Configuration file (.env) not found!
    echo Creating .env from template...
    if exist .env.example (
        copy .env.example .env >nul
    ) else (
        echo [ERROR] .env.example not found!
        pause
        exit /b 1
    )
    echo.
    echo Please edit .env and configure:
    echo   - CAM0, CAM1: Camera indices (e.g., 0, 1)
    echo   - TFLITE_MODEL: Path to model file (e.g., models\mobilenet_ssd_final.tflite)
    echo   - SUPABASE_URL, SUPABASE_ANON_KEY: Cloud sync credentials
    echo.
    echo After configuration, run this script again.
    pause
    exit /b 1
)

REM Check for model
for /f "tokens=2 delims==" %%a in ('findstr TFLITE_MODEL .env') do set MODEL_PATH=%%a
if not exist "%MODEL_PATH%" (
    echo [WARNING] Model not found: %MODEL_PATH%
    echo Please copy your .tflite model to the models\ directory
    echo and update TFLITE_MODEL in .env
    pause
    exit /b 1
)

REM Run application
echo Starting application...
echo.
road-damage-detector.exe
pause
'@

$runBatch | Out-File -FilePath "$RELEASE_DIR\run.bat" -Encoding ASCII

# Create PowerShell run script (alternative)
$runPs1 = @'
# VGTECH Road Damage Detector Launcher (PowerShell)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "VGTECH Road Damage Detector" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "[WARNING] Configuration file (.env) not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from template..."
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
    } else {
        Write-Error "[ERROR] .env.example not found!"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
    Write-Host "Please edit .env and configure:"
    Write-Host "  - CAM0, CAM1: Camera indices (e.g., 0, 1)"
    Write-Host "  - TFLITE_MODEL: Path to model (e.g., models\mobilenet_ssd_final.tflite)"
    Write-Host "  - SUPABASE_URL, SUPABASE_ANON_KEY: Cloud sync credentials"
    Write-Host ""
    Write-Host "After configuration, run this script again."
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for model
$MODEL_PATH = (Get-Content .env | Select-String "TFLITE_MODEL" | ForEach-Object { $_ -replace "TFLITE_MODEL=", "" })
if (-not (Test-Path $MODEL_PATH)) {
    Write-Host "[WARNING] Model not found: $MODEL_PATH" -ForegroundColor Yellow
    Write-Host "Please copy your .tflite model to the models\ directory"
    Write-Host "and update TFLITE_MODEL in .env"
    Read-Host "Press Enter to exit"
    exit 1
}

# Run application
Write-Host "Starting application..." -ForegroundColor Green
Write-Host ""
.\road-damage-detector.exe
Read-Host "Press Enter to exit"
'@

$runPs1 | Out-File -FilePath "$RELEASE_DIR\run.ps1" -Encoding UTF8

# Create README for the release
$releaseReadme = @'
VGTECH Road Damage Detector - Windows Release
==============================================

Quick Start
-----------
1. Extract this archive
2. Edit .env file with your camera and model settings
3. Copy your TFLite model to models\ directory
4. Run: run.bat (or run.ps1 for PowerShell)

Configuration
-------------
Edit .env file:
- CAM0=0                    # First camera index
- CAM1=1                    # Second camera index
- TFLITE_MODEL=models\mobilenet_ssd_final.tflite
- SUPABASE_URL=your_url     # Cloud sync (optional)
- SUPABASE_ANON_KEY=your_key

Camera Calibration (for accurate measurements):
- CAM0_FOCAL_LENGTH=800.0
- CAM0_HEIGHT_CM=150.0
- CAM0_PIXEL_SIZE=0.00375

Requirements
------------
- Windows 10/11 (64-bit)
- USB cameras or built-in webcam
- No additional software needed (standalone .exe)

Camera Setup
------------
- Built-in webcam: Usually CAM0=0
- External USB camera: CAM1=1
- Multiple cameras: Try different indices (0, 1, 2, etc.)

Troubleshooting
---------------
Camera not working:
  - Check Device Manager > Cameras
  - Try different camera indices (0, 1, 2)
  - Allow camera access in Windows Privacy settings

Application won't start:
  - Right-click run.bat > Run as administrator
  - Check Windows Defender/Antivirus settings

For more help, see README.md and QUICKSTART.md

Support
-------
Version: See VERSION file
Changelog: See CHANGELOG.md
'@

$releaseReadme | Out-File -FilePath "$RELEASE_DIR\README-RELEASE.txt" -Encoding UTF8

# Create archive
Write-Host "📦 Creating archive..." -ForegroundColor Yellow
Compress-Archive -Path $RELEASE_DIR -DestinationPath "releases\$RELEASE_NAME.zip" -Force

# Calculate size
$ARCHIVE_SIZE = (Get-Item "releases\$RELEASE_NAME.zip").Length / 1MB
$ARCHIVE_SIZE = [math]::Round($ARCHIVE_SIZE, 2)

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Release archive: releases\$RELEASE_NAME.zip" -ForegroundColor Green
Write-Host "📏 Size: $ARCHIVE_SIZE MB" -ForegroundColor Green
Write-Host ""
Write-Host "To test the release:"
Write-Host "  cd releases\$RELEASE_NAME"
Write-Host "  .\run.bat"
Write-Host ""
Write-Host "To distribute:"
Write-Host "  Upload releases\$RELEASE_NAME.zip to GitHub Releases"
Write-Host ""
