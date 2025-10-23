#!/bin/bash
# Install script for macOS testing
# Run: chmod +x install_mac.sh && ./install_mac.sh

echo "🍎 Installing VGTECH Road Damage Detector for macOS..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install PyQt6
pip install pillow
pip install supabase
pip install python-dotenv

# Check for TFLite
echo "🤖 Installing TensorFlow Lite..."
pip install tensorflow==2.15.0

# Ensure compatible numpy/opencv versions
echo "🧩 Aligning NumPy/OpenCV versions for TensorFlow compatibility..."
pip install --upgrade "numpy==1.26.4"
pip install --upgrade "opencv-python==4.9.0.80"

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Update for Mac
    sed -i '' 's|CAM0=/dev/video0|CAM0=0|' .env
    sed -i '' 's|CAM1=/dev/video1|CAM1=1|' .env
    sed -i '' 's|CAM_WIDTH=1280|CAM_WIDTH=640|' .env
    sed -i '' 's|CAM_HEIGHT=720|CAM_HEIGHT=480|' .env
    
    echo "✅ .env created and configured for macOS"
fi

# Create models directory
mkdir -p models

# Check for model
if [ ! -f "models/mobilenet_ssd_final.tflite" ]; then
    echo "⚠️  TFLite model not found!"
    echo "Please copy mobilenet_ssd_final.tflite to models/ directory"
    echo ""
    echo "Example:"
    echo "  cp ../mobileapps-potholedetection/assets/models/mobilenet_ssd_final.tflite models/"
else
    echo "✅ TFLite model found"
fi

# Create data directory
mkdir -p data

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Copy TFLite model to models/ (if not done)"
echo "  2. Connect USB camera (optional, for testing)"
echo "  3. Run: source venv/bin/activate"
echo "  4. Run: python main.py"
echo ""
echo "🎥 Camera testing on Mac:"
echo "  - Built-in FaceTime camera = index 0"
echo "  - External USB camera = index 1"
echo "  - To test: python -c 'import cv2; cap=cv2.VideoCapture(0); print(cap.isOpened())'"
echo ""
