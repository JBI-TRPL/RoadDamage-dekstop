# 🚀 Quick Start Guide - Jetson Road Damage Detector

## Persiapan Cepat (15 menit)

### 1. Install Dependencies

```bash
cd jetson-road-damage

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Setup Konfigurasi

```bash
# Copy template
cp .env.example .env

# Edit (ganti nilai sesuai kebutuhan)
nano .env
```

**Yang WAJIB diisi:**

```bash
# Lokasi kamera
CAM0_DEVICE=/dev/video0
CAM1_DEVICE=/dev/video1

# Model TFLite (copy dari mobile app)
TFLITE_MODEL=models/mobilenet_ssd_final.tflite

# Supabase (SUDAH BENAR, jangan ubah!)
SUPABASE_URL=https://midjlnxbmvzmtuqurceh.supabase.co
SUPABASE_ANON_KEY=sb_publishable_Fs3XPKYrIt6DIOc5u9K52w_Yf6cNi7g
```

### 3. Copy Model

```bash
# Buat folder models
mkdir -p models

# Copy model TFLite dari mobile app
cp ../mobileapps-potholedetection/assets/models/mobilenet_ssd_final.tflite models/

# Cek ukuran (harus ~3MB)
ls -lh models/
```

### 4. Tes Kamera

```bash
# Cek kamera tersedia
v4l2-ctl --list-devices

# Tes video0
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  video/x-raw,width=640,height=480 ! \
  videoconvert ! autovideosink

# Tes video1
gst-launch-1.0 v4l2src device=/dev/video1 ! \
  video/x-raw,width=640,height=480 ! \
  videoconvert ! autovideosink
```

### 5. Jalankan Aplikasi

```bash
# Pastikan venv aktif
source venv/bin/activate

# Run
python main.py
```

## ✅ Checklist Berhasil

Jika berhasil, harusnya:

- [x] Window muncul dengan judul "VGTECH Road Damage Detector"
- [x] 2 camera feeds terlihat
- [x] Status bar bawah: "Cloud: Connected"
- [x] Jika kamera melihat jalan rusak → kotak muncul + measurement
- [x] Log activity menampilkan deteksi
- [x] Statistics bertambah saat ada deteksi

## 🔧 Troubleshooting Cepat

### Kamera tidak muncul

```bash
# Cek permission
sudo usermod -aG video $USER
# Logout dan login lagi

# Coba device lain
# Di .env ganti ke /dev/video2, /dev/video3, dll
```

### Error "No module named 'PyQt6'"

```bash
# Install ulang
pip uninstall PyQt6
pip install PyQt6
```

### Error "cannot import tflite_runtime"

```bash
# Install tflite untuk ARM
pip install --index-url https://google-coral.github.io/py-repo/ tflite_runtime

# ATAU gunakan TensorFlow full
pip install tensorflow==2.11.0
```

### Cloud tidak connect

```bash
# Test koneksi internet
ping google.com

# Test Supabase
python -c "import requests; print(requests.get('https://midjlnxbmvzmtuqurceh.supabase.co').status_code)"
# Harus return 200
```

### Width/Depth tidak akurat

**PENTING:** Kalibrasi kamera dulu!

```bash
# Edit .env
nano .env

# Sesuaikan dengan kamera Anda:
CAM0_FOCAL_LENGTH=800.0      # Sesuaikan dengan hasil kalibrasi
CAM0_HEIGHT_CM=150.0         # Ukur tinggi kamera dari tanah (cm)
CAM0_PIXEL_SIZE=0.00375      # Cek datasheet kamera
```

**Cara kalibrasi focal length:**

1. Taruh penggaris 30cm di tanah
2. Ambil foto dari ketinggian 100cm
3. Hitung pixel width penggaris di foto (misal: 240px)
4. Rumus: focal_length = (240 × 100) / 30 = **800px**
5. Masukkan ke .env

## 📝 Catatan Penting

### Tinggi Kamera

- **Terlalu rendah (<100cm):** Jarak pandang sempit
- **Terlalu tinggi (>200cm):** Akurasi depth menurun
- **Optimal:** 120-180cm dari tanah
- **Sudut:** Tegak lurus ke bawah atau sedikit miring (<30°)

### Pencahayaan

- **Siang hari:** Terbaik untuk deteksi + depth estimation
- **Mendung:** OK, tapi depth kurang akurat (kurang bayangan)
- **Malam/gelap:** Tambahkan lampu, akurasi menurun

### Kecepatan Kendaraan

- **Berhenti/lambat (<10km/jam):** Terbaik
- **Sedang (10-30km/jam):** OK
- **Cepat (>30km/jam):** Motion blur, deteksi berkurang

## 🎯 Next Steps

Setelah aplikasi jalan:

1. **Kalibrasi kamera** untuk measurement akurat
2. **Tes di jalan nyata** dengan berbagai kondisi
3. **Cek sinkronisasi** - data muncul di Supabase
4. **Monitor performance** - FPS, CPU usage
5. **Tuning parameter** jika perlu (threshold, NMS)

## 📞 Bantuan

Cek log error:

```bash
tail -f road_damage_detector.log
```

Test komponen satu-satu:

```bash
# Test database
python -c "from app.services.database_service import DatabaseService; \
  db = DatabaseService('test.db'); print('DB OK')"

# Test Supabase
python -c "from app.services.supabase_service import SupabaseService; \
  s = SupabaseService('https://midjlnxbmvzmtuqurceh.supabase.co', \
    'sb_publishable_Fs3XPKYrIt6DIOc5u9K52w_Yf6cNi7g', 'detections'); \
  print('Supabase OK' if s.test_connection() else 'Failed')"
```

## 🚗 Selamat Menggunakan!

Jika ada masalah, cek:
- README.md (dokumentasi lengkap)
- road_damage_detector.log (error log)
- Supabase dashboard (data sync)
