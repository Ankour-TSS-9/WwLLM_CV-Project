"""
Simplified Temporal Ball Tracker

A modular ball-tracking system that:
1. Validates candidates using bounding-box properties
2. Associates detections with trajectory predictions
3. Estimates velocity from recent observations
4. Handles rapid movement adaptively
5. Maintains explicit states (DETECTED/PREDICTED/INTERPOLATED/MISSING)
6. Reinitializes after camera cuts
"""

import numpy as np
from collections import deque
from enum import Enum
from typing import Optional, List, Dict, Tuple

from cv import config
from utils import measure_distance


def _frame_scale(frame_shape: Optional[Tuple[int, int]]) -> float:
    if frame_shape is None:
        return 1.0
    frame_height, frame_width = frame_shape[:2]
    reference_area = config.BALL_REFERENCE_FRAME_WIDTH * config.BALL_REFERENCE_FRAME_HEIGHT
    return float(np.sqrt((frame_width * frame_height) / reference_area))


class BallState(Enum):
    """Explicit ball tracking states."""
    DETECTED = "detected"           # High-confidence real detection
    PREDICTED = "predicted"         # Tracker prediction during occlusion
    INTERPOLATED = "interpolated"   # Linear fill between detections
    MISSING = "missing"            # No data available


class BallCandidate:
    """A potential ball detection from YOLO."""
    
    def __init__(self, bbox: List[float], confidence: float, frame_num: int):
        self.bbox = bbox
        self.confidence = confidence
        self.frame_num = frame_num
        self.center = np.array([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2])
        self.width = bbox[2] - bbox[0]
        self.height = bbox[3] - bbox[1]
        self.aspect_ratio = self.width / self.height if self.height > 0 else 0
        self.area = self.width * self.height
    
    def is_valid(
        self,
        min_confidence: Optional[float] = None,
        frame_shape: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Validate candidate using bounding-box properties."""
        scale = _frame_scale(frame_shape)
        min_width = max(1.0, config.BALL_SMALL_MIN_WIDTH_PX * scale)
        min_height = max(1.0, config.BALL_SMALL_MIN_HEIGHT_PX * scale)
        max_width = max(min_width, config.BALL_MAX_WIDTH_PX * scale)
        max_height = max(min_height, config.BALL_MAX_HEIGHT_PX * scale)
        if not (min_width <= self.width <= max_width):
            return False
        if not (min_height <= self.height <= max_height):
            return False
        
        # Aspect ratio (from audit: 0.67-1.14, mean 0.87)
        if not (config.BALL_MIN_ASPECT_RATIO <= self.aspect_ratio <= config.BALL_MAX_ASPECT_RATIO):
            return False
        
        # Confidence floor
        confidence_floor = config.BALL_CONF if min_confidence is None else min_confidence
        if self.confidence < confidence_floor:
            return False
        
        return True


class BallTrajectory:
    """Maintains recent ball observations and velocity estimation."""
    
    def __init__(self, max_history: int = 5):
        self.history = deque(maxlen=max_history)  # Recent (frame, center, state) tuples
        self.detections = deque(maxlen=max_history)
        self.velocity = np.array([0.0, 0.0])      # Estimated velocity (px/frame)
        self.last_detected_frame = None
        self.last_detected_center = None
        self.last_detected_bbox = None
        self.frames_since_detection = 0
    
    def add_detection(self, frame_num: int, center: np.ndarray, bbox=None):
        """Add a real detection to trajectory history."""
        observation = (frame_num, center, BallState.DETECTED)
        self.history.append(observation)
        self.detections.append(observation)
        self.last_detected_frame = frame_num
        self.last_detected_center = center
        self.last_detected_bbox = list(bbox) if bbox is not None else self.last_detected_bbox
        self.frames_since_detection = 0
        self._update_velocity()
    
    def add_prediction(self, frame_num: int, center: np.ndarray):
        """Add a predicted position to trajectory history."""
        self.history.append((frame_num, center, BallState.PREDICTED))
        self.frames_since_detection += 1
    
    def _update_velocity(self):
        """Estimate velocity from recent detections."""
        # Use only real detections for velocity estimation
        detections = [(frame, center) for frame, center, _state in self.detections]
        
        if len(detections) < 2:
            # Not enough data, use zero velocity
            self.velocity = np.array([0.0, 0.0])
            return
        
        # Weighted velocity estimation (more recent = higher weight)
        velocities = []
        for i in range(max(0, len(detections) - 4), len(detections) - 1):
            frame1, center1 = detections[i]
            frame2, center2 = detections[i + 1]
            
            dt = frame2 - frame1
            if dt > 0:
                v = (center2 - center1) / dt
                if np.linalg.norm(v) <= config.BALL_MAX_STEP_PX:
                    velocities.append(v)
        
        if velocities:
            self.velocity = np.median(np.asarray(velocities), axis=0)
        else:
            self.velocity = np.array([0.0, 0.0])
    
    def predict_position(self, frame_num: int) -> Optional[np.ndarray]:
        """Predict ball position at given frame."""
        if not self.history:
            return None
        
        last_frame, last_center, _ = self.history[-1]
        dt = frame_num - last_frame
        
        if dt <= 0:
            return last_center
        
        # Simple linear prediction with velocity
        predicted = last_center + self.velocity * dt
        return predicted
    
    def get_uncertainty(self) -> float:
        """Get current position uncertainty (grows with time since detection)."""
        # Uncertainty grows quadratically with frames since detection
        base_uncertainty = config.BALL_MEASUREMENT_NOISE
        time_factor = 1.0 + 0.5 * self.frames_since_detection
        return base_uncertainty * time_factor
    
    def is_stale(self, current_frame: int) -> bool:
        """Check if trajectory is too old to be reliable."""
        if self.last_detected_frame is None:
            return True
        return (current_frame - self.last_detected_frame) > config.BALL_MAX_PREDICTION_FRAMES
    
    def get_speed(self) -> float:
        """Get current estimated speed (px/frame)."""
        return np.linalg.norm(self.velocity)


class TemporalBallTracker:
    """
    Simplified temporal ball tracker.
    
    Maintains trajectory state and associates detections adaptively.
    """
    
    def __init__(self):
        self.trajectory = BallTrajectory(max_history=5)
        self.is_initialized = False
    
    def reset(self):
        """Reset tracker (e.g., at camera cut)."""
        self.trajectory = BallTrajectory(max_history=5)
        self.is_initialized = False
    
    def process_frame(
        self, 
        candidates: List[BallCandidate], 
        frame_num: int,
        is_camera_cut: bool = False,
        frame_shape: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Optional[BallCandidate], BallState]:
        """
        Process one frame's detections.
        
        Returns:
            (selected_candidate, state) or (None, state)
        """
        # Reset on camera cut
        if is_camera_cut:
            self.reset()
        
        # Filter to valid candidates
        valid_candidates = [
            c for c in candidates
            if c.is_valid(config.BALL_CANDIDATE_CONF, frame_shape)
        ]
        
        # No valid candidates
        if not valid_candidates:
            return self._handle_missing_detection(frame_num)
        
        # Initialize or reinitialize if needed
        if not self.is_initialized:
            primary_candidates = [
                c for c in valid_candidates
                if c.confidence >= config.BALL_CONF
                and c.is_valid(config.BALL_CONF, frame_shape)
            ]
            return self._initialize_with_best_candidate(
                primary_candidates, frame_num, frame_shape
            )
        if self.trajectory.is_stale(frame_num):
            self.reset()
            primary_candidates = [
                c for c in valid_candidates
                if c.confidence >= config.BALL_CONF
                and c.is_valid(config.BALL_CONF, frame_shape)
            ]
            return self._initialize_with_best_candidate(
                primary_candidates, frame_num, frame_shape
            )
        
        # Associate candidate with trajectory
        return self._associate_candidate(valid_candidates, frame_num, frame_shape)
    
    def _initialize_with_best_candidate(
        self, 
        candidates: List[BallCandidate], 
        frame_num: int,
        frame_shape: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Optional[BallCandidate], BallState]:
        """Initialize tracker with the most confident candidate."""
        if not candidates:
            return None, BallState.MISSING
        
        # Select highest confidence candidate
        primary_candidates = [
            c for c in candidates
            if c.confidence >= config.BALL_CONF
            and c.width >= max(1.0, config.BALL_MIN_WIDTH_PX * _frame_scale(frame_shape))
            and c.height >= max(1.0, config.BALL_MIN_HEIGHT_PX * _frame_scale(frame_shape))
        ]
        if not primary_candidates:
            return None, BallState.MISSING
        best = max(primary_candidates, key=lambda c: c.confidence)
        
        self.trajectory.add_detection(frame_num, best.center, best.bbox)
        self.is_initialized = True
        
        return best, BallState.DETECTED
    
    def _associate_candidate(
        self, 
        candidates: List[BallCandidate], 
        frame_num: int,
        frame_shape: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Optional[BallCandidate], BallState]:
        """
        Associate candidates with trajectory prediction.
        
        Uses adaptive gating based on velocity and uncertainty.
        """
        # Predict where ball should be
        predicted_center = self.trajectory.predict_position(frame_num)
        if predicted_center is None:
            return self._initialize_with_best_candidate(candidates, frame_num, frame_shape)
        
        # Get current uncertainty
        uncertainty = self.trajectory.get_uncertainty()
        speed = self.trajectory.get_speed()
        
        # Adaptive gating: allow larger distances for fast movement
        # Base gate: accounts for measurement uncertainty
        # Speed bonus: allow extra distance based on expected travel
        # Acceleration bonus: allow for sudden changes (kicks)
        dt = frame_num - self.trajectory.history[-1][0]
        
        expected_travel = speed * max(1, dt)
        scale = _frame_scale(frame_shape)
        min_gate = max(20.0, config.BALL_ASSOCIATION_MIN_GATE_PX * scale)
        max_gate = max(min_gate, config.BALL_ASSOCIATION_MAX_GATE_PX * scale)
        gate_threshold = min(
            max_gate,
            max(
                min_gate,
                2.0 * expected_travel + 2.0 * uncertainty,
            ),
        )
        
        # Evaluate all candidates
        scored_candidates = []
        for candidate in candidates:
            distance = np.linalg.norm(candidate.center - predicted_center)
            
            # Skip if outside gate
            if distance > gate_threshold:
                continue
            
            # Score combines confidence and distance
            # Closer candidates and higher confidence are preferred
            normalized_distance = distance / (gate_threshold + 1e-6)
            score = candidate.confidence * (1.0 - 0.7 * normalized_distance)
            
            scored_candidates.append((score, distance, candidate))
        
        # No candidates within gate
        if not scored_candidates:
            # Check if we should reinitialize (trajectory may be wrong)
            if self.trajectory.frames_since_detection >= config.BALL_REINITIALIZE_AFTER_FRAMES:
                # Lost track - reinitialize with best candidate
                primary_candidates = [
                    c for c in candidates
                    if c.confidence >= config.BALL_CONF
                    and c.is_valid(config.BALL_CONF, frame_shape)
                ]
                return self._initialize_with_best_candidate(
                    primary_candidates, frame_num, frame_shape
                )
            else:
                # Continue predicting
                return self._handle_missing_detection(frame_num)
        
        # Select best candidate
        best_score, best_distance, best_candidate = max(scored_candidates, key=lambda x: x[0])
        
        # Add to trajectory
        self.trajectory.add_detection(frame_num, best_candidate.center, best_candidate.bbox)
        
        return best_candidate, BallState.DETECTED
    
    def _handle_missing_detection(
        self, 
        frame_num: int
    ) -> Tuple[None, BallState]:
        """Handle frame with no valid detection."""
        if not self.is_initialized:
            return None, BallState.MISSING
        
        # Check if we've lost track
        if self.trajectory.is_stale(frame_num):
            self.is_initialized = False
            return None, BallState.MISSING
        
        # Predict position
        predicted_center = self.trajectory.predict_position(frame_num)
        if predicted_center is not None:
            self.trajectory.add_prediction(frame_num, predicted_center)
            return None, BallState.PREDICTED
        else:
            return None, BallState.MISSING


def interpolate_ball_trajectory(
    ball_positions: List[Dict], 
    max_gap: int = 5,
    camera_cuts: Optional[List[int]] = None
) -> List[Dict]:
    """
    Interpolate missing ball positions between detections.
    
    Does not interpolate:
    - Across camera cuts
    - Across long gaps (> max_gap frames)
    - When step size is too large
    
    Args:
        ball_positions: List of ball position dicts (one per frame)
        max_gap: Maximum gap to interpolate across
        camera_cuts: List of frame numbers with camera cuts
    
    Returns:
        List of ball positions with interpolated data
    """
    if camera_cuts is None:
        camera_cuts = []
    
    camera_cut_set = set(camera_cuts)
    
    # Find frames with real detections
    detected_frames = []
    for frame_num, ball_info in enumerate(ball_positions):
        info = ball_info.get(1, {})
        if info.get('state') == BallState.DETECTED.value:
            detected_frames.append(frame_num)
    
    if len(detected_frames) < 2:
        return ball_positions
    
    # Interpolate between consecutive detections
    result = [dict(info) for info in ball_positions]  # Deep copy
    
    for i in range(len(detected_frames) - 1):
        frame_start = detected_frames[i]
        frame_end = detected_frames[i + 1]
        gap = frame_end - frame_start
        
        # Skip if gap too large
        if gap <= 1 or gap > max_gap:
            continue
        
        # Skip if camera cut in between
        if any(frame_start < cut < frame_end for cut in camera_cut_set):
            continue
        
        # Get start and end positions
        start_info = result[frame_start].get(1, {})
        end_info = result[frame_end].get(1, {})
        
        start_bbox = start_info.get('bbox')
        end_bbox = end_info.get('bbox')
        
        if not start_bbox or not end_bbox:
            continue
        
        # Check step size isn't too large
        start_center = np.array([(start_bbox[0] + start_bbox[2]) / 2, 
                                 (start_bbox[1] + start_bbox[3]) / 2])
        end_center = np.array([(end_bbox[0] + end_bbox[2]) / 2, 
                               (end_bbox[1] + end_bbox[3]) / 2])
        
        step_size = np.linalg.norm(end_center - start_center) / gap
        
        if step_size > config.BALL_MAX_STEP_PX:
            continue
        
        # Linear interpolation
        for frame_num in range(frame_start + 1, frame_end):
            alpha = (frame_num - frame_start) / gap
            
            interp_bbox = [
                start_bbox[0] + alpha * (end_bbox[0] - start_bbox[0]),
                start_bbox[1] + alpha * (end_bbox[1] - start_bbox[1]),
                start_bbox[2] + alpha * (end_bbox[2] - start_bbox[2]),
                start_bbox[3] + alpha * (end_bbox[3] - start_bbox[3]),
            ]
            
            result[frame_num][1] = {
                'bbox': interp_bbox,
                'state': BallState.INTERPOLATED.value,
                'confidence': None,
            }
    
    return result


def run_temporal_tracker(
    detections: List[List[Dict]], 
    camera_cuts: Optional[List[int]] = None
) -> List[Dict]:
    """
    Run temporal ball tracker on full video.
    
    Args:
        detections: List of per-frame detection lists
                   Each detection is dict with 'bbox', 'confidence', 'class_name'
        camera_cuts: Optional list of frame numbers with camera cuts
    
    Returns:
        List of ball positions (one dict per frame)
    """
    tracker = TemporalBallTracker()
    ball_positions = []
    
    if camera_cuts is None:
        camera_cuts = []
    camera_cut_set = set(camera_cuts)
    
    for frame_num, frame_detections in enumerate(detections):
        # Extract ball candidates
        candidates = []
        for det in frame_detections:
            if det.get('class_name') in ('football', 'ball'):
                candidate = BallCandidate(
                    bbox=det['bbox'],
                    confidence=det['confidence'],
                    frame_num=frame_num
                )
                candidates.append(candidate)
        
        # Process frame
        is_cut = frame_num in camera_cut_set
        selected, state = tracker.process_frame(candidates, frame_num, is_camera_cut=is_cut)
        
        # Build result
        if selected is not None:
            ball_positions.append({
                1: {
                    'bbox': selected.bbox,
                    'confidence': selected.confidence,
                    'state': state.value,
                }
            })
        elif state == BallState.PREDICTED:
            # Use predicted position
            predicted_center = tracker.trajectory.predict_position(frame_num)
            if predicted_center is not None:
                # Approximate bbox from previous detection size
                if tracker.trajectory.last_detected_center is not None:
                    last_info = ball_positions[tracker.trajectory.last_detected_frame].get(1, {})
                    last_bbox = last_info.get('bbox')
                    if last_bbox:
                        w = last_bbox[2] - last_bbox[0]
                        h = last_bbox[3] - last_bbox[1]
                        pred_bbox = [
                            predicted_center[0] - w/2,
                            predicted_center[1] - h/2,
                            predicted_center[0] + w/2,
                            predicted_center[1] + h/2,
                        ]
                        ball_positions.append({
                            1: {
                                'bbox': pred_bbox,
                                'confidence': None,
                                'state': state.value,
                            }
                        })
                    else:
                        ball_positions.append({})
                else:
                    ball_positions.append({})
            else:
                ball_positions.append({})
        else:
            ball_positions.append({})
    
    # Interpolate gaps
    ball_positions = interpolate_ball_trajectory(ball_positions, camera_cuts=camera_cuts)
    
    return ball_positions
