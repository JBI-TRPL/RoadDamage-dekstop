#!/usr/bin/env python3
"""
VGTECH Road Damage Detector - Jetson Edition
Main entry point

Usage:
    python main.py

Environment variables (.env):
    # Linux/Jetson: device paths | macOS/Windows: camera indices (0,1)
    CAM0=/dev/video0
    CAM1=/dev/video1
    TFLITE_MODEL=models/mobilenet_ssd_final.tflite
    SUPABASE_URL=https://midjlnxbmvzmtuqurceh.supabase.co
    SUPABASE_ANON_KEY=sb_publishable_Fs3XPKYrIt6DIOc5u9K52w_Yf6cNi7g
"""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ui.main_window import MainWindow
from app import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('road_damage_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set"""
    missing = []

    # Note: On macOS, CAM0_DEVICE can be int 0 (which is falsy), so check for None explicitly
    if getattr(config, "CAM0_DEVICE", None) is None:
        missing.append("CAM0 (or CAM0_DEVICE)")
    if getattr(config, "CAM1_DEVICE", None) is None:
        missing.append("CAM1 (or CAM1_DEVICE)")

    # Model path must exist
    if not config.TFLITE_MODEL_PATH or not Path(config.TFLITE_MODEL_PATH).exists():
        missing.append("TFLITE_MODEL (file not found)")

    # Supabase config
    if not config.SUPABASE_URL or config.SUPABASE_URL == "YOUR_SUPABASE_URL":
        missing.append("SUPABASE_URL")
    if not config.SUPABASE_ANON_KEY or config.SUPABASE_ANON_KEY == "YOUR_SUPABASE_ANON_KEY":
        missing.append("SUPABASE_ANON_KEY")

    return missing


def main():
    """Main application entry point"""
    # Load environment variables
    load_dotenv()
    
    logger.info("🚗 VGTECH Road Damage Detector - Jetson Edition")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")
    
    # Check environment
    missing = check_environment()
    if missing:
        error_msg = (
            "⚠️ Missing or invalid configuration:\n\n" +
            "\n".join(f"- {item}" for item in missing) +
            "\n\nPlease check your .env file!"
        )
        logger.error(error_msg)
        
        # Show error dialog if in GUI mode
        if 'PyQt6' in sys.modules:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Configuration Error", error_msg)
        
        return 1
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("VGTECH Road Damage Detector")
    app.setOrganizationName("VGTECH")
    
    # Create main window
    try:
        window = MainWindow()
        window.show()
        
        logger.info("✅ Application started successfully")
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        
        # Show error dialog
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Failed to start application:\n\n{str(e)}"
        )
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
