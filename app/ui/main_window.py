"""
Main application window
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QStatusBar,
                             QGroupBox, QGridLayout, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont
import numpy as np
import cv2
import logging
from datetime import datetime
from typing import Dict, Optional

from app.services.camera_worker import CameraWorker
from app.services.inference_worker import InferenceWorker
from app.services.classification_worker import ClassificationWorker
from app.services.database_service import DatabaseService
from app.services.supabase_service import SupabaseService
from app.services.measurement_service import MeasurementService
from app import config

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    Main application window for Jetson Road Damage Detector
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚗 VGTECH Road Damage Detector - Jetson Edition")
        self.resize(1600, 900)
        
        # Services
        self.db = DatabaseService(config.DB_PATH)
        self.supabase = SupabaseService(
            config.SUPABASE_URL,
            config.SUPABASE_ANON_KEY,
            config.SUPABASE_TABLE
        )
        
        # Measurement services for each camera
        self.measurement_cam0 = MeasurementService(
            config.CAM0_FOCAL_LENGTH,
            config.CAM0_PIXEL_SIZE,
            config.CAM0_HEIGHT_CM
        )
        
        self.measurement_cam1 = MeasurementService(
            config.CAM1_FOCAL_LENGTH,
            config.CAM1_PIXEL_SIZE,
            config.CAM1_HEIGHT_CM
        )
        
        # Workers
        self.camera_workers = {}
        self.inference_worker = None
        self.classifier_worker = None
        
        # Stats
        self.detection_counts = {cls: 0 for cls in config.ROAD_DAMAGE_CLASSES.values()}
        self.total_detections = 0
        
        # Classification last result
        self._last_classification: Optional[Dict] = None

        # Setup UI
        self._setup_ui()
        
        # Don't auto-start cameras to avoid permission pop-ups; user can start via button
        self.cameras_running = False
        
        # Auto-sync timer
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._auto_sync)
        self.sync_timer.start(config.AUTO_SYNC_INTERVAL * 1000)
        
        logger.info("✅ MainWindow initialized")

    def _setup_ui(self):
        """Setup the user interface"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)

        # Minimal styling for a cleaner look
        self.setStyleSheet(
            """
            QWidget { font-family: -apple-system, Segoe UI, Roboto, Arial; }
            QGroupBox { font-weight: 600; border: 1px solid #ccc; border-radius: 6px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QLabel { font-size: 13px; }
            QPushButton { padding: 6px 10px; }
            """
        )
        
        # Top bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Splitter for cameras and info
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Cameras
        cameras_widget = self._create_cameras_view()
        splitter.addWidget(cameras_widget)
        
        # Right: Stats and log
        info_widget = self._create_info_view()
        splitter.addWidget(info_widget)
        
        splitter.setStretchFactor(0, 3)  # Cameras take 75% width
        splitter.setStretchFactor(1, 1)  # Info takes 25% width
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status()

    def _create_top_bar(self) -> QWidget:
        """Create top control bar"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Title
        title = QLabel("🚗 VGTECH Road Damage Detector")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Start/Stop cameras
        self.btn_toggle_cam = QPushButton("▶️ Start Cameras")
        self.btn_toggle_cam.clicked.connect(self._toggle_cameras)
        layout.addWidget(self.btn_toggle_cam)

        # Sync button
        self.btn_sync = QPushButton("🔄 Sync to Cloud")
        self.btn_sync.clicked.connect(self._sync_now)
        layout.addWidget(self.btn_sync)
        
        # Unsynced count
        self.lbl_unsynced = QLabel("Unsynced: 0")
        layout.addWidget(self.lbl_unsynced)
        
        return widget

    def _create_cameras_view(self) -> QWidget:
        """Create single camera view (cam0)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Single display for detection (cam0)
        cam0_group = QGroupBox("📹 Detection View (cam0)")
        cam0_layout = QVBoxLayout(cam0_group)
        self.lbl_cam0 = QLabel()
        self.lbl_cam0.setMinimumSize(640, 480)
        self.lbl_cam0.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cam0.setStyleSheet("background-color: #1a1a1a; color: white;")
        self.lbl_cam0.setText("Waiting for camera 0...")
        cam0_layout.addWidget(self.lbl_cam0)
        layout.addWidget(cam0_group)
        
        return widget

    def _create_info_view(self) -> QWidget:
        """Create info panel (stats + log)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats
        stats_group = QGroupBox("📊 Detection Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.lbl_stats = {}
        row = 0
        for class_id, class_name in config.ROAD_DAMAGE_CLASSES.items():
            lbl_name = QLabel(f"{class_name}:")
            lbl_count = QLabel("0")
            lbl_count.setStyleSheet("font-weight: bold; font-size: 14px;")
            stats_layout.addWidget(lbl_name, row, 0)
            stats_layout.addWidget(lbl_count, row, 1)
            self.lbl_stats[class_name] = lbl_count
            row += 1
        
        # Total
        stats_layout.addWidget(QLabel("─────────"), row, 0, 1, 2)
        row += 1
        lbl_total_name = QLabel("Total:")
        self.lbl_total = QLabel("0")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 16px; color: #1976D2;")
        stats_layout.addWidget(lbl_total_name, row, 0)
        stats_layout.addWidget(self.lbl_total, row, 1)
        
        layout.addWidget(stats_group)

        # Classifier status
        cls_group = QGroupBox("🧠 Classifier (cam1)")
        cls_layout = QVBoxLayout(cls_group)
        self.lbl_classifier = QLabel("idle")
        cls_layout.addWidget(self.lbl_classifier)
        layout.addWidget(cls_group)
        
        # Log
        log_group = QGroupBox("📝 Activity Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(300)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        return widget

    def _start_workers(self):
        """Start camera and inference workers"""
        if self.cameras_running:
            return
        # Camera 0
        gst0 = config.get_gstreamer_pipeline(
            config.CAM0_DEVICE,
            config.CAM_WIDTH,
            config.CAM_HEIGHT,
            config.CAM_FPS
        )
        self.camera_workers['cam0'] = CameraWorker('cam0', gst0)
        self.camera_workers['cam0'].frame_ready.connect(self._on_frame)
        self.camera_workers['cam0'].error_occurred.connect(self._on_camera_error)
        self.camera_workers['cam0'].start()
        
        # Camera 1
        gst1 = config.get_gstreamer_pipeline(
            config.CAM1_DEVICE,
            config.CAM_WIDTH,
            config.CAM_HEIGHT,
            config.CAM_FPS
        )
        self.camera_workers['cam1'] = CameraWorker('cam1', gst1)
        self.camera_workers['cam1'].frame_ready.connect(self._on_frame)
        self.camera_workers['cam1'].error_occurred.connect(self._on_camera_error)
        self.camera_workers['cam1'].start()
        
        # Inference worker
        self.inference_worker = InferenceWorker(
            config.TFLITE_MODEL_PATH,
            config.CONF_THRESHOLD,
            config.NMS_THRESHOLD
        )
        self.inference_worker.detections_ready.connect(self._on_detections)
        self.inference_worker.start()

        # Classification worker
        self.classifier_worker = ClassificationWorker()
        self.classifier_worker.classification_ready.connect(self._on_classification)
        self.classifier_worker.start()
        
        self.cameras_running = True
        self.btn_toggle_cam.setText("⏸ Stop Cameras")
        self._log("🚀 All workers started")

    def _stop_workers(self):
        if not self.cameras_running:
            return
        for worker in self.camera_workers.values():
            worker.stop()
        self.camera_workers.clear()
        if self.inference_worker:
            self.inference_worker.stop()
            self.inference_worker = None
        if self.classifier_worker:
            self.classifier_worker.stop()
            self.classifier_worker = None
        self.cameras_running = False
        self.btn_toggle_cam.setText("▶️ Start Cameras")
        self._log("🛑 Cameras stopped")

    def _toggle_cameras(self):
        if self.cameras_running:
            self._stop_workers()
        else:
            self._start_workers()

    @pyqtSlot(np.ndarray, str)
    def _on_frame(self, frame: np.ndarray, camera_id: str):
        """Handle new frame from camera"""
        if not self.cameras_running:
            return
        # Send to appropriate worker
        if camera_id == 'cam0' and self.inference_worker:
            self.inference_worker.add_frame(frame, camera_id)
            # Display cam0 frame
            pixmap = self._numpy_to_pixmap(frame)
            self.lbl_cam0.setPixmap(pixmap.scaled(
                self.lbl_cam0.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        elif camera_id == 'cam1' and self.classifier_worker:
            self.classifier_worker.add_frame(frame, camera_id)

    @pyqtSlot(dict)
    def _on_detections(self, result: Dict):
        """Handle detection results"""
        camera_id = result['camera_id']
        boxes = result['boxes']
        classes = result['classes']
        scores = result['scores']
        frame = result['frame']
        
        if len(boxes) == 0:
            return
        
        # Get measurement service for this camera
        measurement = self.measurement_cam0 if camera_id == 'cam0' else self.measurement_cam1
        
        # Draw boxes and save detections
        h, w = frame.shape[:2]
        for bbox, class_idx, score in zip(boxes, classes, scores):
            class_name = config.ROAD_DAMAGE_CLASSES[class_idx]
            # If we have a recent classification from cam1 and it's confident, show alongside
            cls_text = None
            if self._last_classification and (time := self._last_classification.get('ts')):
                # use within 3 seconds
                from time import time as now
                if now() - time < 3.0 and self._last_classification.get('confidence', 0) >= config.CLASSIFIER_CONF_THRESHOLD:
                    cls_label = self._last_classification.get('label')
                    cls_conf = self._last_classification.get('confidence')
                    cls_text = f"cls:{cls_label} {cls_conf:.0%}"
            color = config.CLASS_COLORS.get(class_name, (0, 255, 0))
            
            # Measure width and depth
            width_cm, depth_cm = measurement.measure_damage(frame, bbox)
            
            # Draw bounding box
            y1, x1, y2, x2 = bbox
            pt1 = (int(x1 * w), int(y1 * h))
            pt2 = (int(x2 * w), int(y2 * h))
            cv2.rectangle(frame, pt1, pt2, color, 2)
            
            # Draw label with measurements
            label = f"{class_name} {score:.0%}"
            label2 = f"W:{width_cm}cm D:{depth_cm}cm"
            if cls_text:
                label2 += f" | {cls_text}"
            cv2.putText(frame, label, (pt1[0], max(0, pt1[1] - 25)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, label2, (pt1[0], max(0, pt1[1] - 5)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Save to database
            detection = {
                'camera_id': camera_id,
                'road_class': class_name,
                'confidence': score,
                'width_cm': width_cm,
                'depth_cm': depth_cm,
                'bbox_x1': x1,
                'bbox_y1': y1,
                'bbox_x2': x2,
                'bbox_y2': y2,
                'synced': 0
            }
            try:
                self.db.insert_detection(detection)
            except Exception as e:
                logger.exception(f"DB insert failed: {e}")
                self._log(f"❌ DB insert failed: {e}")
            
            # Update stats
            self.detection_counts[class_name] += 1
            self.total_detections += 1
            
            self._log(f"🔍 {camera_id}: {class_name} ({score:.0%}) - W:{width_cm}cm D:{depth_cm}cm")
        
        # Update UI
        self._update_stats()
        self._update_status()
        
        # Display only cam0 frames with boxes
        if camera_id == 'cam0':
            pixmap = self._numpy_to_pixmap(frame)
            self.lbl_cam0.setPixmap(pixmap.scaled(
                self.lbl_cam0.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    @pyqtSlot(str, str)
    def _on_camera_error(self, error: str, camera_id: str):
        """Handle camera errors"""
        self._log(f"❌ {camera_id}: {error}")

    def _on_classification(self, payload: Dict):
        """Handle classification result from cam1"""
        self._last_classification = payload
        self.lbl_classifier.setText(f"{payload['label']} ({payload['confidence']:.0%})")

    def _sync_now(self):
        """Sync unsynced detections to Supabase"""
        self._log("🔄 Syncing to Supabase...")
        
        # Get unsynced rows
        rows = self.db.get_unsynced(limit=200)
        
        if len(rows) == 0:
            self._log("✅ No pending detections to sync")
            return
        
        # Upload to Supabase
        success = self.supabase.upsert_detections(rows)
        
        if success:
            # Mark as synced
            ids = [row['id'] for row in rows]
            self.db.mark_synced(ids)
            self._log(f"✅ Synced {len(rows)} detections to cloud")
        else:
            self._log(f"❌ Failed to sync detections (offline?)")
        
        self._update_status()

    def _auto_sync(self):
        """Auto-sync timer callback"""
        unsynced = self.db.get_unsynced_count()
        if unsynced > 0:
            self._sync_now()

    def _update_stats(self):
        """Update statistics labels"""
        for class_name, count in self.detection_counts.items():
            if class_name in self.lbl_stats:
                self.lbl_stats[class_name].setText(str(count))
        
        self.lbl_total.setText(str(self.total_detections))

    def _update_status(self):
        """Update status bar"""
        try:
            total = self.db.get_total_count()
            unsynced = self.db.get_unsynced_count()
        except Exception as e:
            logger.exception(f"DB status failed: {e}")
            total, unsynced = 0, 0
        
        status = f"Total: {total} | Unsynced: {unsynced}"
        
        if self.supabase.is_available:
            status += " | ☁️ Cloud: Connected"
        else:
            status += " | ⚠️ Cloud: Offline"
        
        self.status_bar.showMessage(status)
        self.lbl_unsynced.setText(f"Unsynced: {unsynced}")

    def _log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _numpy_to_pixmap(self, frame: np.ndarray) -> QPixmap:
        """Convert numpy array to QPixmap"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        return QPixmap.fromImage(img)

    def closeEvent(self, event):
        """Handle window close"""
        logger.info("🛑 Shutting down...")
        
        # Stop workers
        self._stop_workers()
        
        # Close database
        self.db.close()
        
        logger.info("✅ Shutdown complete")
        event.accept()
