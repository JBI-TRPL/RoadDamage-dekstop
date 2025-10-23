"""
Configuration module for Jetson Road Damage Detector
"""
import os
import sys
import platform
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Detect platform
IS_JETSON = platform.machine() in ['aarch64', 'arm64'] and platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux' and not IS_JETSON

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Camera Configuration
if IS_MAC:
    # Mac uses index-based camera access
    CAM0_DEVICE = int(os.getenv("CAM0", "0"))
    CAM1_DEVICE = int(os.getenv("CAM1", "1"))
else:
    # Linux/Jetson uses device path
    CAM0_DEVICE = os.getenv("CAM0", "/dev/video0")
    CAM1_DEVICE = os.getenv("CAM1", "/dev/video1")

CAM_WIDTH = int(os.getenv("CAM_WIDTH", "640"))
CAM_HEIGHT = int(os.getenv("CAM_HEIGHT", "480"))
CAM_FPS = int(os.getenv("CAM_FPS", "30"))

# Model Configuration (robust path resolution)
_model_env = os.getenv("TFLITE_MODEL", "mobilenet_ssd_final.tflite")
_model_path = Path(_model_env)

if _model_path.is_absolute():
    TFLITE_MODEL_PATH = str(_model_path)
else:
    # Try relative to project root first (supports values like "models/.../file.tflite")
    candidate = PROJECT_ROOT / _model_path
    if candidate.exists():
        TFLITE_MODEL_PATH = str(candidate)
    else:
        # Fallback to models directory with just the filename
        TFLITE_MODEL_PATH = str(MODELS_DIR / _model_path.name)

CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.50"))
NMS_THRESHOLD = float(os.getenv("NMS_THRESHOLD", "0.45"))

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "detections")

# Camera Calibration
CAM0_FOCAL_LENGTH = float(os.getenv("CAM0_FOCAL_LENGTH", "800.0"))
CAM0_PIXEL_SIZE = float(os.getenv("CAM0_PIXEL_SIZE", "0.00375"))
CAM0_HEIGHT_CM = float(os.getenv("CAM0_HEIGHT_CM", "150.0"))

CAM1_FOCAL_LENGTH = float(os.getenv("CAM1_FOCAL_LENGTH", "800.0"))
CAM1_PIXEL_SIZE = float(os.getenv("CAM1_PIXEL_SIZE", "0.00375"))
CAM1_HEIGHT_CM = float(os.getenv("CAM1_HEIGHT_CM", "150.0"))

# Stereo Configuration
STEREO_BASELINE_CM = float(os.getenv("STEREO_BASELINE_CM", "30.0"))
ENABLE_STEREO_DEPTH = os.getenv("ENABLE_STEREO_DEPTH", "false").lower() == "true"

# UI Configuration
THEME = os.getenv("THEME", "Fusion")
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "#1976D2")

# Auto-sync Configuration
AUTO_SYNC_INTERVAL = int(os.getenv("AUTO_SYNC_INTERVAL", "60"))

# Detection thresholds
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.5"))
NMS_THRESHOLD = float(os.getenv("NMS_THRESHOLD", "0.45"))
INPUT_SIZE = 320

# Optional secondary classifier (for cam1)
_cls_env = os.getenv("CLASSIFIER_MODEL", "")
CLASSIFIER_MODEL_PATH = None
if _cls_env:
    _cls_path = Path(_cls_env)
    if _cls_path.is_absolute() and _cls_path.exists():
        CLASSIFIER_MODEL_PATH = str(_cls_path)
    else:
        cand = PROJECT_ROOT / _cls_path
        if cand.exists():
            CLASSIFIER_MODEL_PATH = str(cand)
        else:
            # fallback: look in models dir
            cand2 = MODELS_DIR / _cls_path.name
            CLASSIFIER_MODEL_PATH = str(cand2) if cand2.exists() else None

CLASSIFIER_INPUT_SIZE = int(os.getenv("CLASSIFIER_INPUT_SIZE", "224"))
CLASSIFIER_CONF_THRESHOLD = float(os.getenv("CLASSIFIER_CONF_THRESHOLD", "0.6"))

# Database Configuration
DB_PATH = str(DATA_DIR / os.getenv("DB_PATH", "app.db").split("/")[-1])

# Road Damage Classes
ROAD_DAMAGE_CLASSES = {
    0: 'amblas',
    1: 'bergelombang',
    2: 'berlubang',
    3: 'retak_buaya'
}

# Class Colors (for bounding boxes)
CLASS_COLORS = {
    'amblas': (255, 0, 0),        # Red
    'bergelombang': (255, 165, 0), # Orange
    'berlubang': (0, 0, 255),      # Blue
    'retak_buaya': (255, 255, 0)   # Yellow
}

def get_gstreamer_pipeline(device: str, width: int, height: int, fps: int) -> str:
    """
    Build GStreamer pipeline for camera
    Platform-aware: Mac uses direct VideoCapture, Jetson uses GStreamer
    """
    if IS_MAC:
        # Mac doesn't need GStreamer pipeline, return None
        # camera_worker.py will use cv2.VideoCapture(device) directly
        return None
    else:
        # Linux/Jetson uses GStreamer for USB camera
        return (
            f"v4l2src device={device} ! "
            f"video/x-raw, width={width}, height={height}, framerate={fps}/1 ! "
            f"videoconvert ! appsink drop=true sync=false"
        )

def get_csi_pipeline(sensor_id: int, width: int, height: int, fps: int) -> str:
    """
    Build GStreamer pipeline for CSI camera on Jetson (e.g., IMX219)
    """
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={width}, height={height}, framerate={fps}/1, format=NV12 ! "
        f"nvvidconv flip-method=0 ! "
        f"video/x-raw, format=BGRx ! videoconvert ! appsink drop=true sync=false"
    )
