"""
Classification worker thread for secondary camera (cam1)
Uses either a dedicated classifier model if provided, or falls back to
aggregating class probabilities from the same SSD model (frame-level class).
"""
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import cv2
import time
import logging
from typing import Optional, Tuple
from queue import Queue, Empty

from app import config

logger = logging.getLogger(__name__)

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    try:
        from tensorflow.lite.python.interpreter import Interpreter
    except ImportError:
        logger.warning("⚠️ Neither tflite_runtime nor tensorflow.lite available for classifier")
        Interpreter = None


class ClassificationWorker(QThread):
    """
    Worker thread to perform lightweight classification on cam1 frames.
    Emits the most recent classification label with confidence.
    """
    classification_ready = pyqtSignal(dict)  # {label, class_idx, confidence, ts}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._frame_queue: Queue[Tuple[np.ndarray, str]] = Queue(maxsize=2)
        self._interpreter: Optional[object] = None
        self._use_classifier = False

    def add_frame(self, frame: np.ndarray, camera_id: str):
        try:
            self._frame_queue.put_nowait((frame, camera_id))
        except:
            pass

    def run(self):
        self._running = True

        if Interpreter is None:
            logger.error("❌ No TFLite interpreter for classification")
            return

        try:
            # Decide which model to load
            model_path = config.CLASSIFIER_MODEL_PATH or config.TFLITE_MODEL_PATH
            self._use_classifier = config.CLASSIFIER_MODEL_PATH is not None
            logger.info(f"🔄 Loading classifier model: {model_path} (dedicated={self._use_classifier})")
            self._interpreter = Interpreter(model_path=model_path)
            self._interpreter.allocate_tensors()

            input_details = self._interpreter.get_input_details()
            output_details = self._interpreter.get_output_details()

            if self._use_classifier:
                # Assume a single output vector of class probs
                in_h, in_w = input_details[0]['shape'][1:3]
                preprocess_size = (in_w, in_h)
                classify_fn = self._classify_with_classifier
            else:
                # Fallback to SSD: aggregate per-anchor class probs to frame-level
                in_h, in_w = input_details[0]['shape'][1:3]
                preprocess_size = (in_w, in_h)
                self._ssd_output_details = output_details
                classify_fn = self._classify_with_ssd

            while self._running:
                try:
                    frame, cam_id = self._frame_queue.get(timeout=0.2)
                except Empty:
                    continue

                if cam_id != 'cam1':
                    continue

                # Preprocess
                inp = self._preprocess(frame, preprocess_size)
                self._interpreter.set_tensor(input_details[0]['index'], inp)

                # Inference
                t0 = time.time()
                self._interpreter.invoke()
                infer_ms = (time.time() - t0) * 1000

                # Classify
                class_idx, conf = classify_fn()
                label = config.ROAD_DAMAGE_CLASSES.get(class_idx, str(class_idx))

                self.classification_ready.emit({
                    'label': label,
                    'class_idx': int(class_idx),
                    'confidence': float(conf),
                    'inference_time': infer_ms,
                    'ts': time.time()
                })

        except Exception as e:
            logger.error(f"❌ Classification error: {e}")

    def _preprocess(self, frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        img = cv2.resize(frame, size)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        return img

    def _classify_with_classifier(self) -> Tuple[int, float]:
        # Assume single output prob vector
        output = self._interpreter.get_output_details()[0]
        probs = self._interpreter.get_tensor(output['index'])[0]
        class_idx = int(np.argmax(probs))
        conf = float(np.max(probs))
        return class_idx, conf

    def _classify_with_ssd(self) -> Tuple[int, float]:
        # SSD fallback: take max prob over anchors for each class
        # Output 1 assumed to be classes: [1, A, C]
        classes = self._interpreter.get_tensor(self._ssd_output_details[1]['index'])[0]
        # Aggregate across anchors
        agg = classes.max(axis=0)
        class_idx = int(np.argmax(agg))
        conf = float(np.max(agg))
        return class_idx, conf

    def stop(self):
        logger.info("🛑 Stopping classification worker...")
        self._running = False
        self.wait(2000)
