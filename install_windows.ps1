# Windows install script for VGTECH Road Damage Detector
# Usage (PowerShell as Administrator):
#   Set-ExecutionPolicy Bypass -Scope Process -Force
#   .\install_windows.ps1

Write-Host "🟦 Installing VGTECH Road Damage Detector for Windows..." -ForegroundColor Cyan

# 1) Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python not found. Please install Python 3.10+ from https://www.python.org/downloads/ and re-run."
  exit 1
}

$pyVer = (python --version)
Write-Host "✅ $pyVer"

# 2) Create venv
Write-Host "📦 Creating virtual environment..."
python -m venv venv

# 3) Activate venv
$venvActivate = "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
  & $venvActivate
} else {
  Write-Error "Failed to activate venv."
  exit 1
}

# 4) Upgrade pip
Write-Host "⬆️  Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# 5) Install core packages
Write-Host "📥 Installing Python packages (PyQt6, Pillow, dotenv, requests)..."
pip install PyQt6 pillow python-dotenv requests

# 6) OpenCV and NumPy
Write-Host "🎥 Installing OpenCV..."
pip install opencv-python

# 7) TFLite or TensorFlow fallback
Write-Host "🤖 Installing TensorFlow Lite Runtime (Windows, if available)..."
try {
  pip install tflite-runtime -ErrorAction Stop
} catch {
  Write-Warning "tflite-runtime wheel not available. Falling back to TensorFlow (CPU)."
  pip install tensorflow==2.15.0
}

# 8) Supabase client
Write-Host "☁️ Installing Supabase client..."
pip install supabase

# 9) .env setup
if (-not (Test-Path .env)) {
  Write-Host "📝 Creating .env from template..."
  Copy-Item .env.example .env
  # Update camera indices for Windows (0 and 1 by default)
  (Get-Content .env) |
    ForEach-Object { $_ -replace 'CAM0=/dev/video0', 'CAM0=0' } |
    ForEach-Object { $_ -replace 'CAM1=/dev/video1', 'CAM1=1' } |
    Set-Content .env
}

# 10) Ensure folders
New-Item -ItemType Directory -Force -Path models | Out-Null
New-Item -ItemType Directory -Force -Path data | Out-Null

# 11) Model check
if (-not (Test-Path "models/mobilenet_ssd_final.tflite")) {
  Write-Warning "Model not found: models/mobilenet_ssd_final.tflite"
  Write-Host "Copy the TFLite model from the mobile app assets:"
  Write-Host "  copy ..\mobileapps-potholedetection\assets\models\mobilenet_ssd_final.tflite models\"
} else {
  Write-Host "✅ Model found"
}

Write-Host ""
Write-Host "✅ Installation complete." -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1) venv\\Scripts\\Activate.ps1"
Write-Host "  2) python main.py"
Write-Host "  3) If camera doesn't open, try a different index (CAM0=1) in .env"
