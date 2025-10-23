#!/bin/bash
# Build script for Linux release
# Usage: ./build_release_linux.sh

set -e

echo "🔨 Building VGTECH Road Damage Detector for Linux..."

# Read version
VERSION=$(cat VERSION)
echo "Version: $VERSION"

# Check if venv is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not active. Activating..."
    source venv/bin/activate
fi

# Install PyInstaller if not present
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build executable
echo "🚀 Building executable..."
pyinstaller build-linux.spec

# Create release directory
RELEASE_DIR="releases/vgtech-road-damage-detector-v${VERSION}-linux"
mkdir -p "$RELEASE_DIR"

# Copy built files
echo "📦 Packaging release..."
cp -r dist/road-damage-detector-linux/* "$RELEASE_DIR/"
cp VERSION "$RELEASE_DIR/"
cp README.md "$RELEASE_DIR/"
cp CHANGELOG.md "$RELEASE_DIR/"
cp .env.example "$RELEASE_DIR/.env"
cp -r models "$RELEASE_DIR/" 2>/dev/null || echo "⚠️  No models directory, copy manually"

# Create run script
cat > "$RELEASE_DIR/run.sh" << 'EOF'
#!/bin/bash
# Run VGTECH Road Damage Detector

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env not found. Creating from template..."
    cp .env.example .env
    echo "Please edit .env and configure your settings:"
    echo "  - CAM0, CAM1 (camera devices)"
    echo "  - TFLITE_MODEL (model path)"
    echo "  - SUPABASE_URL, SUPABASE_ANON_KEY"
    exit 1
fi

# Run application
./road-damage-detector
EOF

chmod +x "$RELEASE_DIR/run.sh"

# Create archive
echo "📦 Creating archive..."
cd releases
tar -czf "vgtech-road-damage-detector-v${VERSION}-linux-x64.tar.gz" "vgtech-road-damage-detector-v${VERSION}-linux"
cd ..

echo "✅ Build complete!"
echo "Release: releases/vgtech-road-damage-detector-v${VERSION}-linux-x64.tar.gz"
echo ""
echo "To test:"
echo "  cd releases/vgtech-road-damage-detector-v${VERSION}-linux"
echo "  ./run.sh"
