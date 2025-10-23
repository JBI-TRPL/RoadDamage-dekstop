"""
Inference worker thread for running TFLite model
"""
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import cv2
import time
import logging
from typing import Dict, List, Tuple, Optional
from queue import Queue, Empty

logger = logging.getLogger(__name__)

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    try:
        from tensorflow.lite.python.interpreter import Interpreter
    except ImportError:
        logger.warning("⚠️ Neither tflite_runtime nor tensorflow.lite available")
        Interpreter = None

class InferenceWorker(QThread):
    """
    Worker thread for TFLite inference
    """
    detections_ready = pyqtSignal(dict)  # {camera_id, boxes, classes, scores, frame}
    
    def __init__(self, 
                 model_path: str,
                 conf_threshold: float = 0.5,
                 nms_threshold: float = 0.45,
                 parent=None):
        """
        Initialize inference worker
        
        Args:
            model_path: Path to TFLite model
            conf_threshold: Confidence threshold
            nms_threshold: NMS IoU threshold
            parent: Parent QObject
        """
        super().__init__(parent)
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self._running = False
        self._frame_queue = Queue(maxsize=4)  # Limit queue size
        self._interpreter = None

    def add_frame(self, frame: np.ndarray, camera_id: str):
        """
        Add frame to inference queue
        
        Args:
            frame: BGR image
            camera_id: Camera identifier
        """
        try:
            # Try to add without blocking, drop if queue is full
            self._frame_queue.put_nowait((frame, camera_id))
        except:
            # Queue full, skip this frame
            pass

    def run(self):
        """Main thread loop for inference"""
        self._running = True
        
        if Interpreter is None:
            logger.error("❌ TFLite interpreter not available")
            return
        
        try:
            # Load model
            logger.info(f"🔄 Loading TFLite model: {self.model_path}")
            self._interpreter = Interpreter(model_path=self.model_path)
            self._interpreter.allocate_tensors()
            
            input_details = self._interpreter.get_input_details()
            output_details = self._interpreter.get_output_details()
            
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"   Input shape: {input_details[0]['shape']}")
            logger.info(f"   Output shapes: {[od['shape'] for od in output_details]}")
            
            # Get model input size
            input_shape = input_details[0]['shape']
            model_height, model_width = input_shape[1], input_shape[2]
            
            inference_count = 0
            
            while self._running:
                try:
                    # Get frame from queue (timeout to check _running flag)
                    frame, camera_id = self._frame_queue.get(timeout=0.1)
                except Empty:
                    continue
                
                # Preprocess
                input_data = self._preprocess(frame, model_width, model_height)
                
                # Inference
                start_time = time.time()
                self._interpreter.set_tensor(input_details[0]['index'], input_data)
                self._interpreter.invoke()
                inference_time = (time.time() - start_time) * 1000
                
                # Get outputs
                # Output 0: boxes [1, 172, 4]
                # Output 1: classes [1, 172, 4]
                boxes = self._interpreter.get_tensor(output_details[0]['index'])[0]
                classes = self._interpreter.get_tensor(output_details[1]['index'])[0]
                
                # Post-process
                detections = self._postprocess(boxes, classes, frame)
                
                inference_count += 1
                if inference_count % 30 == 0:
                    logger.debug(f"🧠 Inference #{inference_count}: {inference_time:.1f}ms")
                
                # Emit results
                self.detections_ready.emit({
                    'camera_id': camera_id,
                    'boxes': detections['boxes'],
                    'classes': detections['classes'],
                    'scores': detections['scores'],
                    'frame': frame,
                    'inference_time': inference_time
                })
                
        except Exception as e:
            logger.error(f"❌ Inference error: {e}")
            import traceback
            traceback.print_exc()

    def _preprocess(self, frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Preprocess frame for model input
        
        Args:
            frame: BGR image
            width: Model input width
            height: Model input height
            
        Returns:
            Preprocessed input tensor
        """
        # Resize
        img = cv2.resize(frame, (width, height))
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0-1 (float32)
        img = img.astype(np.float32) / 255.0
        
        # Add batch dimension
        img = np.expand_dims(img, axis=0)
        
        return img

    def _postprocess(self, 
                    boxes: np.ndarray,
                    classes: np.ndarray,
                    frame: np.ndarray) -> Dict:
        """
        Post-process model outputs
        
        Args:
            boxes: [172, 4] bounding boxes (cy, cx, h, w) normalized
            classes: [172, 4] class probabilities
            frame: Original frame for filtering
            
        Returns:
            Dictionary with filtered detections
        """
        valid_boxes = []
        valid_classes = []
        valid_scores = []
        
        h, w = frame.shape[:2]
        
        for i in range(len(boxes)):
            # Get class probabilities
            class_probs = classes[i]
            
            # Get max probability and class index
            max_conf = np.max(class_probs)
            class_idx = np.argmax(class_probs)
            
            # Filter by confidence
            if max_conf < self.conf_threshold:
                continue
            
            # Get box coordinates (center format)
            cy, cx, bh, bw = boxes[i]
            
            # Filter by Y position (skip upper 20% of image - sky/background)
            if cy < 0.2:
                continue
            
            # Filter by area
            area = bh * bw
            if area < 0.02 or area > 0.80:
                continue
            
            # Convert center format to corner format
            y1 = cy - bh / 2
            x1 = cx - bw / 2
            y2 = cy + bh / 2
            x2 = cx + bw / 2
            
            # Clamp to [0, 1]
            y1 = max(0, min(y1, 1))
            x1 = max(0, min(x1, 1))
            y2 = max(0, min(y2, 1))
            x2 = max(0, min(x2, 1))
            
            valid_boxes.append([y1, x1, y2, x2])
            valid_classes.append(int(class_idx))
            valid_scores.append(float(max_conf))
        
        # Apply NMS if we have detections
        if len(valid_boxes) > 0:
            keep_indices = self._apply_nms(valid_boxes, valid_scores)
            
            valid_boxes = [valid_boxes[i] for i in keep_indices]
            valid_classes = [valid_classes[i] for i in keep_indices]
            valid_scores = [valid_scores[i] for i in keep_indices]
        
        return {
            'boxes': valid_boxes,
            'classes': valid_classes,
            'scores': valid_scores
        }

    def _apply_nms(self, boxes: List, scores: List) -> List[int]:
        """
        Apply Non-Maximum Suppression
        
        Args:
            boxes: List of [y1, x1, y2, x2] normalized boxes
            scores: List of confidence scores
            
        Returns:
            List of indices to keep
        """
        if len(boxes) == 0:
            return []
        
        boxes = np.array(boxes)
        scores = np.array(scores)
        
        # Get coordinates
        y1 = boxes[:, 0]
        x1 = boxes[:, 1]
        y2 = boxes[:, 2]
        x2 = boxes[:, 3]
        
        # Calculate areas
        areas = (y2 - y1) * (x2 - x1)
        
        # Sort by score
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            # Calculate IoU with rest
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            # Keep boxes with IoU less than threshold
            inds = np.where(iou <= self.nms_threshold)[0]
            order = order[inds + 1]
        
        return keep

    def stop(self):
        """Stop the inference worker"""
        logger.info("🛑 Stopping inference worker...")
        self._running = False
        self.wait(2000)
