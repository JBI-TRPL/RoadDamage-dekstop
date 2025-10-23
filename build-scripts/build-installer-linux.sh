#!/bin/bash
# Installer script for VGTECH Road Damage Detector (Linux)
# This script builds and packages the application as a standalone executable

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "════════════════════════════════════════════════════════"
echo "  VGTECH Road Damage Detector - Linux Installer Builder"
echo "════════════════════════════════════════════════════════"
echo ""

# Read version
if [ ! -f VERSION ]; then
    echo "❌ VERSION file not found!"
    exit 1
fi

VERSION=$(cat VERSION)
echo "📦 Building version: $VERSION"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Install PyInstaller
echo "📥 Installing PyInstaller..."
pip install pyinstaller -q

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build executable using spec file
echo "🔨 Building standalone executable..."
if [ -f "build-linux.spec" ]; then
    pyinstaller build-linux.spec --clean
else
    echo "❌ build-linux.spec not found!"
    exit 1
fi

# Create release directory
RELEASE_NAME="vgtech-road-damage-detector-v${VERSION}-linux-x64"
RELEASE_DIR="releases/$RELEASE_NAME"
mkdir -p "$RELEASE_DIR"

echo "📦 Packaging release..."

# Copy built files
cp -r dist/road-damage-detector-linux/* "$RELEASE_DIR/"

# Copy documentation
cp VERSION "$RELEASE_DIR/"
cp README.md "$RELEASE_DIR/"
cp CHANGELOG.md "$RELEASE_DIR/"
cp QUICKSTART.md "$RELEASE_DIR/" 2>/dev/null || true

# Copy example config
cp .env.example "$RELEASE_DIR/.env"

# Copy models if present
if [ -d "models" ]; then
    mkdir -p "$RELEASE_DIR/models"
    cp models/*.tflite "$RELEASE_DIR/models/" 2>/dev/null || echo "⚠️  No .tflite models found in models/"
fi

# Create data directory
mkdir -p "$RELEASE_DIR/data"

# Create run script
cat > "$RELEASE_DIR/run.sh" << 'RUNSCRIPT'
#!/bin/bash
# VGTECH Road Damage Detector Launcher

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚗 VGTECH Road Damage Detector"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Configuration file (.env) not found!"
    echo "Creating .env from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
    echo ""
    echo "Please edit .env and configure:"
    echo "  - CAM0, CAM1: Camera device paths (e.g., /dev/video0, /dev/video1)"
    echo "  - TFLITE_MODEL: Path to model file (e.g., models/mobilenet_ssd_final.tflite)"
    echo "  - SUPABASE_URL, SUPABASE_ANON_KEY: Cloud sync credentials"
    echo ""
    echo "After configuration, run this script again."
    exit 1
fi

# Check for model
MODEL_PATH=$(grep TFLITE_MODEL .env | cut -d'=' -f2)
if [ ! -f "$MODEL_PATH" ]; then
    echo "⚠️  Model not found: $MODEL_PATH"
    echo "Please copy your .tflite model to the models/ directory"
    echo "and update TFLITE_MODEL in .env"
    exit 1
fi

# Check camera permissions (Linux)
if [ "$(uname)" == "Linux" ]; then
    if ! groups | grep -q video; then
        echo "⚠️  User not in 'video' group. Camera access may fail."
        echo "Run: sudo usermod -aG video $USER"
        echo "Then logout and login again."
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Run application
echo "🚀 Starting application..."
./road-damage-detector
RUNSCRIPT

chmod +x "$RELEASE_DIR/run.sh"

# Create README for the release
cat > "$RELEASE_DIR/README-RELEASE.txt" << 'RELEASEREADME'
VGTECH Road Damage Detector - Linux Release
============================================

Quick Start
-----------
1. Extract this archive
2. Edit .env file with your camera and model settings
3. Copy your TFLite model to models/ directory
4. Run: ./run.sh

Configuration
-------------
Edit .env file:
- CAM0=/dev/video0          # First camera device
- CAM1=/dev/video1          # Second camera device
- TFLITE_MODEL=models/mobilenet_ssd_final.tflite
- SUPABASE_URL=your_url     # Cloud sync (optional)
- SUPABASE_ANON_KEY=your_key

Camera Calibration (for accurate measurements):
- CAM0_FOCAL_LENGTH=800.0
- CAM0_HEIGHT_CM=150.0
- CAM0_PIXEL_SIZE=0.00375

Requirements
------------
- Linux (Ubuntu 18.04+, Jetson Nano)
- USB cameras or CSI cameras
- Camera permissions (user in 'video' group)

Troubleshooting
---------------
Camera not found:
  sudo usermod -aG video $USER
  # Then logout/login

For more help, see README.md and QUICKSTART.md

Support
-------
Version: See VERSION file
Changelog: See CHANGELOG.md
RELEASEREADME

# Create archive
echo "📦 Creating archive..."
cd releases
tar -czf "${RELEASE_NAME}.tar.gz" "$RELEASE_NAME"
cd ..

# Calculate size
ARCHIVE_SIZE=$(du -h "releases/${RELEASE_NAME}.tar.gz" | cut -f1)

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Build complete!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📦 Release archive: releases/${RELEASE_NAME}.tar.gz"
echo "📏 Size: $ARCHIVE_SIZE"
echo ""
echo "To test the release:"
echo "  cd releases/$RELEASE_NAME"
echo "  ./run.sh"
echo ""
echo "To distribute:"
echo "  Upload releases/${RELEASE_NAME}.tar.gz to GitHub Releases"
echo ""
