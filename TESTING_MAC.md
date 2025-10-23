# 🍎 Testing on macOS

Quick guide untuk testing aplikasi desktop di Mac sebelum deploy ke Jetson.

## ⚡ Quick Install

```bash
cd jetson-road-damage

# Run install script
chmod +x install_mac.sh
./install_mac.sh

# Copy model
cp ../mobileapps-potholedetection/assets/models/mobilenet_ssd_final.tflite models/

# Run
source venv/bin/activate
python main.py
```

## 🎥 Camera di Mac

### Built-in Camera
- **FaceTime HD Camera**: Index 0
- Di `.env`: `CAM0=0`

### USB Camera
- **External USB**: Index 1 (biasanya)
- Di `.env`: `CAM1=1`

### Test Camera

```bash
# Test camera 0 (built-in)
python -c "import cv2; cap=cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"

# Test camera 1 (USB)
python -c "import cv2; cap=cv2.VideoCapture(1); print('OK' if cap.isOpened() else 'FAIL')"

# Show camera frame
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print(f'Frame shape: {frame.shape}')
    cv2.imshow('Test', frame)
    cv2.waitKey(0)
cap.release()
"
```

## 🔧 Perbedaan Mac vs Jetson

| Fitur | Mac | Jetson |
|-------|-----|--------|
| **Camera API** | `cv2.VideoCapture(0)` | GStreamer pipeline |
| **Camera Index** | 0, 1, 2... | /dev/video0, /dev/video1 |
| **TFLite** | `tensorflow.lite` | `tflite_runtime` |
| **Resolution** | 640x480 (default) | 1280x720 (optimal) |
| **Performance** | CPU only | GPU accelerated |

## ⚙️ Configuration (.env for Mac)

```bash
# Camera (menggunakan index, bukan device path)
CAM0=0          # Built-in camera
CAM1=1          # USB camera (jika ada)
CAM_WIDTH=640
CAM_HEIGHT=480
CAM_FPS=30

# Model (sama dengan Jetson)
TFLITE_MODEL=models/mobilenet_ssd_final.tflite

# Supabase (sama dengan mobile app & Jetson)
SUPABASE_URL=https://midjlnxbmvzmtuqurceh.supabase.co
SUPABASE_ANON_KEY=sb_publishable_Fs3XPKYrIt6DIOc5u9K52w_Yf6cNi7g
SUPABASE_TABLE=detections

# Detection
CONF_THRESHOLD=0.5
NMS_THRESHOLD=0.45

# Calibration (perkiraan untuk testing)
CAM0_FOCAL_LENGTH=800.0
CAM0_PIXEL_SIZE=0.00375
CAM0_HEIGHT_CM=150.0

CAM1_FOCAL_LENGTH=800.0
CAM1_PIXEL_SIZE=0.00375
CAM1_HEIGHT_CM=150.0
```

## 🚀 Running

```bash
# Activate venv
source venv/bin/activate

# Run application
python main.py
```

On first launch, the UI shows one camera display. Click "▶️ Start Cameras" to start both cameras:
- cam0 renders the live video and detections
- cam1 runs classification; the label shows in the right panel
- Click again to stop cameras

### Expected Output

```
🚗 VGTECH Road Damage Detector - Jetson Edition
Python: 3.x.x
Working directory: /path/to/jetson-road-damage
✅ Application started successfully
```

Window akan muncul dengan:
- 2 camera feeds (jika ada 2 camera)
- Statistics panel
- Activity log
- Status bar

## 📸 Testing Detection

Untuk test detection di Mac:

1. **Gunakan gambar jalan rusak:**
```bash
# Edit camera_worker.py untuk test dengan gambar
# (Atau buka aplikasi, tunjukkan gambar jalan rusak ke camera)
```

2. **Atau gunakan video:**
```bash
# Download test video jalan rusak
# Tunjukkan ke camera built-in
```

3. **Best: Print foto jalan rusak**
- Print gambar jalan rusak (berlubang, retak, dll)
- Tunjukkan ke camera
- Lihat bounding box + measurements

## 🐛 Troubleshooting Mac

### Camera tidak muncul

```bash
# Check camera permission
# System Preferences → Security & Privacy → Camera
# Allow Terminal/Python

# Test dengan native tool
system_profiler SPCameraDataType

# List cameras
python -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera {i}: Available')
        cap.release()
"
```

### PyQt6 error on Mac M1/M2

```bash
# Install Rosetta 2 (jika belum)
softwareupdate --install-rosetta

# Install PyQt6 dengan pip
pip install PyQt6

# Atau gunakan conda
conda install -c conda-forge pyqt
```

### TensorFlow Lite error

```bash
# Uninstall tflite-runtime
pip uninstall tflite-runtime

# Install full TensorFlow
pip install tensorflow==2.15.0
```

### Camera permission denied

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Camera**
2. Check **Terminal** or **Python**
3. Restart terminal
4. Run again

## ⚠️ Limitations on Mac

1. **Single camera testing**: Mac biasanya hanya punya 1 built-in camera
   - Bisa beli USB camera untuk test dual camera
   
2. **CPU inference**: Slower than Jetson GPU
   - FPS akan lebih rendah
   - Normal untuk testing
   
3. **Measurement accuracy**: Camera calibration harus sesuai Mac camera
   - Nilai di .env hanya perkiraan
   - Untuk production, calibrate di Jetson
   
4. **No GStreamer optimization**: Direct OpenCV
   - Lebih simple tapi kurang optimal
   - Di Jetson akan jauh lebih cepat

## ✅ What to Test on Mac

- [x] UI muncul dengan benar
- [x] Camera feed terlihat
- [x] Detection bounding box muncul (jika tunjukkan jalan rusak)
- [x] Statistics update
- [x] Activity log menampilkan deteksi
- [x] Supabase sync berhasil (cek cloud)
- [x] Database local tersimpan (cek data/app.db)

## 🎯 Production Deployment

**Mac hanya untuk testing UI/logic!**

Untuk production:
1. Test di Mac dulu (UI, sync, database)
2. Copy project ke Jetson Nano
3. Calibrate camera di Jetson
4. Test dengan kamera real di Jetson
5. Deploy di kendaraan

## 📝 Notes

- Aplikasi **otomatis detect platform** (Mac vs Jetson)
- Config di `app/config.py` sudah platform-aware
- Camera worker otomatis pilih mode (direct vs GStreamer)
- Kode yang sama jalan di Mac dan Jetson ✨

## 🔗 Next Steps

After testing on Mac:
1. Verify Supabase sync works
2. Check database schema
3. Test with mobile app (sync data)
4. Deploy to Jetson for production
