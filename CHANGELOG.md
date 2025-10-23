# Changelog

All notable changes to VGTECH Road Damage Detector will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-24

### Added
- Initial release of desktop application
- Dual-camera support: cam0 for detection, cam1 for classification
- Real-time road damage detection using MobileNet-SSD TFLite model
- Physical measurement estimation (width and depth in cm)
- Edge-based measurement refinement using Canny edge detection
- Supabase cloud synchronization for detections
- SQLite local database with offline support
- Start/Stop camera button for manual control
- Single-screen UI with clean design
- Statistics panel showing detection counts by class
- Activity log showing recent detections
- Platform support: macOS, Linux/Jetson Nano, Windows
- Installation scripts for each platform
- Configurable camera calibration for accurate measurements
- Auto-sync to cloud at configurable intervals
- Classification worker for frame-level class prediction

### Features
- **Detection Classes**: amblas, bergelombang, berlubang, retak_buaya
- **Measurement**: Monocular width/depth estimation with camera calibration
- **Edge Detection**: Canny-based refinement for better accuracy
- **Dual Camera**: One for detection, one for classification/verification
- **Cloud Sync**: Automatic upload to Supabase with retry logic
- **Offline Mode**: Local SQLite caching when cloud unavailable

### Platform-specific
- **Linux/Jetson**: GStreamer pipeline for camera capture with GPU acceleration support
- **macOS**: Direct OpenCV VideoCapture with TensorFlow Lite
- **Windows**: Direct VideoCapture with TFLite runtime

### Known Limitations
- Depth estimation is heuristic-based (not true stereo)
- Classification model is optional (falls back to SSD aggregation)
- Camera calibration required for accurate measurements
- macOS/Windows use single camera index, Linux uses device paths

---

## Release Types

### Semantic Versioning
- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.X.0): New features, backward-compatible
- **PATCH** (0.0.X): Bug fixes, backward-compatible

### Example Future Releases
- **1.0.1**: Bug fix release (e.g., fix sync retry logic)
- **1.1.0**: Add stereo depth support
- **2.0.0**: Change database schema (breaking change)
