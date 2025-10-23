"""
Camera worker thread for capturing frames from camera
"""
from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

class CameraWorker(QThread):
    """
    Worker thread for camera capture using GStreamer
    """
    frame_ready = pyqtSignal(np.ndarray, str)  # frame, camera_id
    error_occurred = pyqtSignal(str, str)  # error_message, camera_id
    
    def __init__(self, camera_id: str, gst_pipeline: str, parent=None):
        """
        Initialize camera worker
        
        Args:
            camera_id: Unique camera identifier (e.g., 'cam0', 'cam1')
            gst_pipeline: GStreamer pipeline string
            parent: Parent QObject
        """
        super().__init__(parent)
        self.camera_id = camera_id
        self.gst_pipeline = gst_pipeline
        self._running = False
        self._cap = None

    def run(self):
        """Main thread loop for capturing frames"""
        self._running = True
        
        try:
            # Open camera
            if self.gst_pipeline is None:
                # Mac/Windows: Direct camera access by index
                camera_idx = int(self.camera_id.replace('cam', ''))
                logger.info(f"📷 Opening {self.camera_id} at index {camera_idx} (direct mode)")
                self._cap = cv2.VideoCapture(camera_idx)
            else:
                # Jetson/Linux: GStreamer pipeline
                logger.info(f"📷 Opening {self.camera_id}: {self.gst_pipeline}")
                self._cap = cv2.VideoCapture(self.gst_pipeline, cv2.CAP_GSTREAMER)
            
            if not self._cap.isOpened():
                error_msg = f"Failed to open {self.camera_id}"
                logger.error(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg, self.camera_id)
                return
            
            logger.info(f"✅ {self.camera_id} opened successfully")
            # Try to reduce internal buffering to mitigate lag
            try:
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            
            frame_count = 0
            while self._running:
                ret, frame = self._cap.read()
                
                if not ret:
                    logger.warning(f"⚠️ {self.camera_id}: Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Emit frame
                self.frame_ready.emit(frame.copy(), self.camera_id)
                frame_count += 1
                
                if frame_count % 300 == 0:  # Log every 300 frames (~20s at 15fps)
                    logger.debug(f"📹 {self.camera_id}: {frame_count} frames captured")
                
                # Small delay to prevent 100% CPU usage
                time.sleep(0.001)
                
        except Exception as e:
            error_msg = f"Exception in {self.camera_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg, self.camera_id)
            
        finally:
            if self._cap is not None:
                self._cap.release()
                logger.info(f"🔒 {self.camera_id} closed")

    def stop(self):
        """Stop the camera worker"""
        logger.info(f"🛑 Stopping {self.camera_id}...")
        self._running = False
        self.wait(2000)  # Wait up to 2 seconds for thread to finish

    def is_running(self) -> bool:
        """Check if worker is running"""
        return self._running
