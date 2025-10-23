#!/usr/bin/env bash
# Jetson Nano/NX install script for VGTECH Road Damage Detector
# Usage: chmod +x install_jetson.sh && ./install_jetson.sh

set -e

echo "🟢 Installing dependencies for Jetson..."

# 1) System packages
sudo apt update
sudo apt install -y \
  python3-venv python3-pip python3-dev \
  gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-libav libgstreamer1.0-dev \
  libopencv-dev python3-opencv \
  qtbase5-dev

echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "⬆️  Upgrading pip..."
pip install --upgrade pip wheel setuptools

echo "📥 Installing Python packages..."
# Core UI and utilities
pip install PyQt6 pillow python-dotenv requests

echo "🎥 Installing OpenCV..."
pip install opencv-python

echo "🤖 Installing TensorFlow Lite Runtime (Jetson)..."
set +e
pip install --index-url https://google-coral.github.io/py-repo/ tflite_runtime
TFL_STATUS=$?
set -e

if [ $TFL_STATUS -ne 0 ]; then
  echo "⚠️  tflite_runtime install failed, falling back to TensorFlow (CPU)."
  pip install tensorflow==2.11.0
fi

echo "☁️ Installing Supabase client..."
pip install supabase

# .env setup
if [ ! -f .env ]; then
  echo "📝 Creating .env from template..."
  cp .env.example .env
  # Keep Linux device paths; set a reasonable default resolution
  sed -i 's|CAM_WIDTH=1280|CAM_WIDTH=1280|' .env
  sed -i 's|CAM_HEIGHT=720|CAM_HEIGHT=720|' .env
  echo "✅ .env created"
fi

# Ensure folders
mkdir -p models data

echo "📁 Model check..."
if [ ! -f "models/mobilenet_ssd_final.tflite" ]; then
  echo "⚠️  Model not found: models/mobilenet_ssd_final.tflite"
  echo "Copy the TFLite model from the mobile app assets:"
  echo "  cp ../mobileapps-potholedetection/assets/models/mobilenet_ssd_final.tflite models/"
else
  echo "✅ Model found"
fi

echo "🚀 Done. Next steps:"
echo "  1) source venv/bin/activate"
echo "  2) python main.py"
echo "  3) If cameras fail, run: sudo usermod -aG video $USER && reboot"
