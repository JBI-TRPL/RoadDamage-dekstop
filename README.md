# 🚗 VGTECH Road Damage Detector - Jetson Edition

Desktop application for real-time road damage detection on NVIDIA Jetson Nano with automatic cloud synchronization.

## 🎯 Features

- **Dual Camera Support**: Monitor 2 cameras simultaneously
- **Real-time Detection**: MobileNet-SSD TFLite model (same as mobile app)
- **Physical Measurements**: Automatic width and depth estimation
- **Cloud Sync**: Automatic synchronization with Supabase (shared with mobile app)
- **Modern UI**: PyQt6 interface with live camera feeds and statistics
- **Local Cache**: SQLite database for offline operation

## 📋 Requirements

### Hardware
- NVIDIA Jetson Nano (4GB recommended)
- 2x USB cameras (or CSI cameras)
- SD card (32GB+)
- Power supply (5V 4A)

### Software
- Ubuntu 18.04+ (JetPack 4.6+)
- Python 3.8+
- GStreamer 1.14+

## 🚀 Installation

You can use the platform-specific installers or follow the manual steps below.

Quick installers:

- macOS: see TESTING_MAC.md or run `./install_mac.sh`
- Jetson (Nano/NX): run `./install_jetson.sh`
- Windows: run `./install_windows.ps1`

### 1. System Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3-pip python3-dev

# Install GStreamer
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    libgstreamer1.0-dev

# Install OpenCV dependencies
sudo apt install -y \
    libopencv-dev \
    python3-opencv

# Install Qt dependencies
sudo apt install -y \
    libqt6-dev \
    qt6-base-dev
```

### 2. Project Setup

```bash
# Clone or copy project
cd /path/to/project
cd jetson-road-damage

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Model Setup

```bash
# Create models directory
mkdir -p models

# Copy TFLite model (same as mobile app)
cp /path/to/mobilenet_ssd_final.tflite models/

# Verify model
ls -lh models/mobilenet_ssd_final.tflite
```

### 4. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required settings:**

```bash
# Camera Devices (Linux/Jetson use device paths; macOS/Windows use indices like 0,1)
CAM0=/dev/video0
CAM1=/dev/video1

# Model Path
TFLITE_MODEL=models/mobilenet_ssd_final.tflite

# Supabase (SAME AS MOBILE APP)
SUPABASE_URL=https://midjlnxbmvzmtuqurceh.supabase.co
SUPABASE_ANON_KEY=sb_publishable_Fs3XPKYrIt6DIOc5u9K52w_Yf6cNi7g

# Camera Calibration (IMPORTANT for accurate measurements)
CAM0_FOCAL_LENGTH=800.0
CAM0_PIXEL_SIZE=0.00375
CAM0_HEIGHT_CM=150.0

CAM1_FOCAL_LENGTH=800.0
CAM1_PIXEL_SIZE=0.00375
CAM1_HEIGHT_CM=150.0
```

### 5. Camera Calibration (Critical)

**Why calibrate?**
Accurate width/depth measurements require knowing:
- Focal length (in pixels)
- Camera height from ground (in cm)
- Pixel size (sensor specification)

**Calibration steps:**

1. **Get Focal Length:**
```bash
# Take photo of ruler at known distance
# Measure: focal_length = (pixel_width × distance) / object_width

# Example:
# - Ruler width: 30cm
# - Distance: 100cm
# - Pixel width in image: 240px
# focal_length = (240 × 100) / 30 = 800px
```

2. **Measure Camera Height:**
```bash
# Measure from ground to camera lens center
# Example: 150cm (1.5 meters)
```

3. **Get Pixel Size:**
```bash
# Check camera sensor datasheet
# Common values:
# - IMX219 (Raspberry Pi Camera v2): 0.00375mm
# - OV5647: 0.0014mm
# - USB webcam: ~0.005-0.01mm
```

4. **Update .env:**
```bash
CAM0_FOCAL_LENGTH=800.0
CAM0_HEIGHT_CM=150.0
CAM0_PIXEL_SIZE=0.00375
```

## 🎮 Usage

### Run Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run
python main.py
```

When the window opens:
- Click "▶️ Start Cameras" to begin streaming. The app now shows a single live view (cam0) for detection.
- cam1 runs as a classifier in the background; its current label appears in the right panel and is overlaid on detections when confident.
- Click the button again to stop both cameras cleanly.

### Camera Check

```bash
# List available cameras
v4l2-ctl --list-devices

# Test camera with GStreamer
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! autovideosink
```

### First Run Checklist

- [ ] Both camera feeds visible
- [ ] Detections appear with bounding boxes
- [ ] Width/depth measurements shown
- [ ] Activity log shows detections
- [ ] Statistics update in real-time
- [ ] "Cloud: Connected" in status bar
- [ ] Sync button uploads to Supabase

## 🔧 Troubleshooting

### Camera Not Found

```bash
# Check camera permissions
ls -l /dev/video*
sudo usermod -aG video $USER

# Reboot
sudo reboot
```

### GStreamer Pipeline Error

```bash
# Test pipeline manually
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  video/x-raw,width=640,height=480 ! \
  videoconvert ! autovideosink

# If error, try different format
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  video/x-raw,format=UYVY,width=640,height=480 ! \
  videoconvert ! autovideosink
```

### TFLite Import Error

```bash
# Install tflite-runtime for ARM
pip install --index-url https://google-coral.github.io/py-repo/ tflite_runtime

# OR install full TensorFlow
pip install tensorflow==2.11.0
```

### Supabase Sync Failed

```bash
# Test connection
python -c "from app.services.supabase_service import SupabaseService; \
  s = SupabaseService('YOUR_URL', 'YOUR_KEY', 'detections'); \
  print('Connected!' if s.test_connection() else 'Failed')"

# Check table exists in Supabase
# Go to: https://midjlnxbmvzmtuqurceh.supabase.co
# SQL Editor → Run:
SELECT * FROM detections LIMIT 1;
```

### Measurements Incorrect

**Width too large/small:**
- Check focal_length calibration
- Verify camera_height is correct
- Ensure camera is perpendicular to ground

**Depth always similar:**
- Depth is estimated (not measured directly)
- Requires good lighting for shadow detection
- Consider adding stereo camera for true depth

## 📊 Database Schema

### Local SQLite (`detections.db`)

```sql
CREATE TABLE detections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  camera_id TEXT NOT NULL,         -- 'cam0' or 'cam1'
  road_class TEXT NOT NULL,        -- 'amblas', 'bergelombang', 'berlubang', 'retak_buaya'
  confidence REAL NOT NULL,        -- 0.0 - 1.0
  width_cm REAL,                   -- Estimated width in cm
  depth_cm REAL,                   -- Estimated depth in cm
  bbox_x1 REAL,                    -- Bounding box coordinates (0-1)
  bbox_y1 REAL,
  bbox_x2 REAL,
  bbox_y2 REAL,
  latitude REAL,                   -- GPS (optional)
  longitude REAL,
  image_path TEXT,                 -- Saved image path (optional)
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  synced INTEGER DEFAULT 0         -- 0 = not synced, 1 = synced
);
```

### Supabase Cloud (`detections` table)

**Same schema as mobile app** - data from both devices will sync to same table.

## 🔄 Auto-Sync Behavior

- **Interval**: Every 30 seconds (configurable in `config.py`)
- **Batch size**: 200 records per sync
- **Offline mode**: Saves locally until connection restored
- **Conflict resolution**: Uses `upsert` (last write wins)

## 🎨 UI Overview

```
┌─────────────────────────────────────────────────────────────┐
│ 🚗 VGTECH Road Damage Detector       [🔄 Sync] Unsynced: 0 │
├─────────────────────────────────────┬───────────────────────┤
│                                     │ 📊 Statistics         │
│  📹 Camera 0                        │                       │
│  ┌─────────────────────────────┐   │  amblas: 12           │
│  │                             │   │  bergelombang: 5      │
│  │   [Live Feed with Boxes]    │   │  berlubang: 23        │
│  │                             │   │  retak_buaya: 8       │
│  └─────────────────────────────┘   │  ─────────────        │
│                                     │  Total: 48            │
│  📹 Camera 1                        │                       │
│  ┌─────────────────────────────┐   ├───────────────────────┤
│  │                             │   │ 📝 Activity Log       │
│  │   [Live Feed with Boxes]    │   │                       │
│  │                             │   │ [12:34:56] cam0:      │
│  └─────────────────────────────┘   │   berlubang (85%)     │
│                                     │   W:45cm D:8cm        │
└─────────────────────────────────────┴───────────────────────┘
Total: 48 | Unsynced: 0 | ☁️ Cloud: Connected
```

## 🔐 Security Notes

- Supabase anon key is safe for client apps (row-level security applies)
- Never commit `.env` file to git
- Camera devices require user to be in `video` group

## 📝 Development

```bash
# Enable debug logging
# Edit main.py:
logging.basicConfig(level=logging.DEBUG, ...)

# Test without cameras (use video files)
# Edit config.py:
def get_gstreamer_pipeline(...):
    return f"filesrc location=test_video.mp4 ! decodebin ! videoconvert ! appsink"

# Run tests (if added)
pytest tests/
```

## 🚀 Performance Tips

### Jetson Nano Optimization

1. **Maximize power mode:**
```bash
sudo nvpmodel -m 0  # 10W mode
sudo jetson_clocks   # Max clocks
```

2. **GPU acceleration:**
```bash
# Use GPU-accelerated OpenCV
pip uninstall opencv-python
# Install opencv-contrib-python with CUDA support
```

3. **Reduce camera resolution** (if slow):
```bash
# In .env:
CAM_WIDTH=320
CAM_HEIGHT=240
```

4. **Increase inference interval** (if CPU maxed):
```bash
# In config.py:
INFERENCE_INTERVAL = 0.2  # Process every 200ms instead of every frame
```

## 📄 License

Same as main project.

## 🆘 Support

- Check logs: `tail -f road_damage_detector.log`
- Test components individually (camera, model, database, Supabase)
- Verify Supabase table exists and is accessible

## 🔗 Related

- **Mobile App**: `road_damage_detector/` (Flutter)
- **Training Notebook**: `Road Damage Detection MobileNetSSD.ipynb`
- **Model**: `mobilenet_ssd_final.tflite`
