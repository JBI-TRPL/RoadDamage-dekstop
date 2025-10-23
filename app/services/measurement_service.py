"""
Measurement service for estimating width and depth of road damage
"""
import numpy as np
import cv2
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MeasurementService:
    """
    Service for measuring road damage dimensions using camera calibration
    """
    
    def __init__(self, 
                 focal_length: float,
                 pixel_size: float,
                 camera_height_cm: float):
        """
        Initialize measurement service
        
        Args:
            focal_length: Camera focal length in pixels
            pixel_size: Physical size of one pixel (mm)
            camera_height_cm: Height of camera from ground in cm
        """
        self.focal_length = focal_length
        self.pixel_size = pixel_size
        self.camera_height_cm = camera_height_cm
        
        logger.info(f"📏 MeasurementService initialized:")
        logger.info(f"   Focal length: {focal_length}px")
        logger.info(f"   Pixel size: {pixel_size}mm")
        logger.info(f"   Camera height: {camera_height_cm}cm")

    def calculate_distance(self, bbox_bottom_y: float, image_height: int) -> float:
        """
        Calculate distance to object using similar triangles
        
        Args:
            bbox_bottom_y: Y coordinate of bottom of bounding box (normalized 0-1)
            image_height: Height of image in pixels
            
        Returns:
            Distance in cm
        """
        # Convert normalized to pixel
        bottom_px = bbox_bottom_y * image_height
        
        # Distance from center (assuming camera points down at angle)
        # Simple approximation: farther from bottom = farther away
        center_y = image_height / 2
        offset_from_center = abs(bottom_px - center_y)
        
        # Using pinhole camera model
        # distance = (focal_length * real_height) / pixel_height
        # For ground plane: distance ≈ camera_height * focal_length / offset
        
        if offset_from_center < 10:  # Too close to center, use default
            return self.camera_height_cm
        
        distance = (self.camera_height_cm * self.focal_length) / offset_from_center
        return max(50, min(distance, 500))  # Clamp between 50-500cm

    def estimate_width(self, 
                      bbox: Tuple[float, float, float, float],
                      image_width: int,
                      image_height: int) -> float:
        """
        Estimate physical width of damage in cm
        
        Args:
            bbox: Bounding box (y1, x1, y2, x2) normalized 0-1
            image_width: Width of image in pixels
            image_height: Height of image in pixels
            
        Returns:
            Estimated width in cm
        """
        y1, x1, y2, x2 = bbox
        
        # Get distance to object
        bbox_bottom_y = max(y1, y2)
        distance = self.calculate_distance(bbox_bottom_y, image_height)
        
        # Calculate pixel width
        pixel_width = abs(x2 - x1) * image_width
        
        # Convert pixel width to physical width using distance
        # physical_width = (pixel_width * distance) / focal_length
        width_cm = (pixel_width * distance) / self.focal_length
        
        return round(width_cm, 1)

    def estimate_depth(self, 
                      bbox: Tuple[float, float, float, float],
                      image_width: int,
                      image_height: int,
                      intensity_variance: Optional[float] = None) -> float:
        """
        Estimate physical depth of damage in cm
        
        For monocular depth, we use heuristics:
        1. Larger bounding box area often indicates shallower damage (more visible)
        2. Higher intensity variance indicates deeper damage (more shadows)
        
        Args:
            bbox: Bounding box (y1, x1, y2, x2) normalized 0-1
            image_width: Width of image in pixels
            image_height: Height of image in pixels
            intensity_variance: Variance of pixel intensities in bbox (optional)
            
        Returns:
            Estimated depth in cm (approximation)
        """
        y1, x1, y2, x2 = bbox
        
        # Calculate bbox area (normalized)
        bbox_area = (x2 - x1) * (y2 - y1)
        
        # Heuristic 1: Larger area = shallower (0.5-3cm)
        # Smaller area = deeper (3-15cm)
        area_depth = 15 * (1 - bbox_area) if bbox_area < 0.5 else 3 * (1 - bbox_area)
        
        # Heuristic 2: Use intensity variance if available
        if intensity_variance is not None:
            # Higher variance (more shadows) = deeper
            # Normalize variance (0-1) and scale to depth (0-10cm)
            variance_depth = min(intensity_variance * 10, 10)
            
            # Combine both heuristics
            depth_cm = (area_depth + variance_depth) / 2
        else:
            depth_cm = area_depth
        
        # Clamp depth to reasonable range
        return round(max(0.5, min(depth_cm, 20)), 1)

    def calculate_intensity_variance(self, 
                                    frame: np.ndarray,
                                    bbox: Tuple[float, float, float, float]) -> float:
        """
        Calculate intensity variance within bounding box
        
        Args:
            frame: BGR image
            bbox: Bounding box (y1, x1, y2, x2) normalized 0-1
            
        Returns:
            Normalized variance (0-1)
        """
        h, w = frame.shape[:2]
        y1, x1, y2, x2 = bbox
        
        # Convert to pixel coordinates
        x1_px = int(x1 * w)
        y1_px = int(y1 * h)
        x2_px = int(x2 * w)
        y2_px = int(y2 * h)
        
        # Extract ROI
        roi = frame[y1_px:y2_px, x1_px:x2_px]
        
        if roi.size == 0:
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Calculate variance
        variance = np.var(gray)
        
        # Normalize (typical variance range: 0-10000)
        normalized_variance = min(variance / 10000, 1.0)
        
        return normalized_variance

    def measure_damage(self,
                      frame: np.ndarray,
                      bbox: Tuple[float, float, float, float],
                      calculate_variance: bool = True) -> Tuple[float, float]:
        """
        Measure both width and depth of damage, with edge-based refinement.
        
        Args:
            frame: BGR image
            bbox: Bounding box (y1, x1, y2, x2) normalized 0-1
            calculate_variance: Whether to calculate intensity variance for depth
            
        Returns:
            Tuple of (width_cm, depth_cm)
        """
        h, w = frame.shape[:2]
        
        # Baseline width from bbox
        width_cm_bbox = self.estimate_width(bbox, w, h)
        
        # Edge-based refinement
        edge_w_px, edge_h_px, edge_strength = self._edge_metrics(frame, bbox)
        if edge_w_px > 0:
            # Convert edge width in pixels to cm using same distance model
            y1, x1, y2, x2 = bbox
            distance = self.calculate_distance(max(y1, y2), h)
            width_cm_edges = (edge_w_px * distance) / self.focal_length
            # Blend: trust edges slightly more when strong
            alpha = min(0.8, 0.4 + 0.4 * edge_strength)
            width_cm = round(alpha * width_cm_edges + (1 - alpha) * width_cm_bbox, 1)
        else:
            width_cm = width_cm_bbox
        
        # Depth estimation
        if calculate_variance:
            variance = self.calculate_intensity_variance(frame, bbox)
            depth_cm = self.estimate_depth(bbox, w, h, variance)
        else:
            depth_cm = self.estimate_depth(bbox, w, h)
        
        # Use vertical edge presence to gently adjust depth (more edges -> deeper)
        if edge_h_px > 0:
            depth_cm = round(min(20.0, depth_cm + min(3.0, 3.0 * edge_strength)), 1)
        
        logger.debug(f"📏 Measured (refined): width={width_cm}cm, depth={depth_cm}cm")
        
        return width_cm, depth_cm

    def _edge_metrics(self,
                      frame: np.ndarray,
                      bbox: Tuple[float, float, float, float]) -> Tuple[int, int, float]:
        """
        Compute simple edge metrics inside the bbox ROI using Canny.
        Returns (edge_width_px, edge_height_px, edge_strength[0-1]).
        """
        h, w = frame.shape[:2]
        y1, x1, y2, x2 = bbox
        x1_px = max(0, min(int(x1 * w), w - 1))
        y1_px = max(0, min(int(y1 * h), h - 1))
        x2_px = max(0, min(int(x2 * w), w - 1))
        y2_px = max(0, min(int(y2 * h), h - 1))
        
        roi = frame[y1_px:y2_px, x1_px:x2_px]
        if roi.size == 0 or roi.shape[0] < 5 or roi.shape[1] < 5:
            return 0, 0, 0.0
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 50, 150)
        
        # Horizontal and vertical edge profiles
        vert_profile = edges.sum(axis=0)  # per column
        horiz_profile = edges.sum(axis=1)  # per row
        
        if vert_profile.max() == 0 or horiz_profile.max() == 0:
            return 0, 0, 0.0
        
        # Count columns/rows that exceed 20% of max -> effective spans
        v_thresh = 0.2 * vert_profile.max()
        h_thresh = 0.2 * horiz_profile.max()
        edge_width_px = int((vert_profile > v_thresh).sum())
        edge_height_px = int((horiz_profile > h_thresh).sum())
        
        # Edge strength as normalized mean
        edge_strength = float(min(1.0, (edges.mean() / 255.0) * 2.0))
        
        return edge_width_px, edge_height_px, edge_strength
