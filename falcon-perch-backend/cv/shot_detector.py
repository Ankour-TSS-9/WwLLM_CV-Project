"""
Broadcast shot detection and classification for football video analysis.

Detects shot boundaries using frame difference and histogram analysis,
then classifies each shot into tactical categories.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class ShotType(Enum):
    """Shot classification categories."""
    WIDE_TACTICAL = "wide_tactical"  # Full pitch view for tactical analysis
    MEDIUM_GAMEPLAY = "medium_gameplay"  # Medium view showing gameplay
    CLOSE_UP = "close_up"  # Player close-ups, celebrations, etc.
    REPLAY = "replay"  # Replay or non-live view
    STADIUM = "stadium"  # Stadium, crowd, bench views
    UNCERTAIN = "uncertain"  # Unable to classify confidently


class TransitionType(Enum):
    """Transition between shots."""
    HARD_CUT = "hard_cut"  # Instant cut
    GRADUAL = "gradual"  # Fade, dissolve, wipe
    CONTINUOUS = "continuous"  # No transition


@dataclass
class Shot:
    """Represents a continuous shot segment."""
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    shot_type: ShotType
    confidence: float  # 0.0 to 1.0
    transition_in: TransitionType
    transition_out: Optional[TransitionType]
    
    # Technical indicators
    green_ratio: float  # Ratio of green pixels (pitch visibility)
    edge_density: float  # Edge density (higher = more detail)
    motion_level: float  # Average motion in shot
    
    # Shot-specific flags
    pitch_calibration_valid: bool = False
    camera_motion_valid: bool = False
    metrics_enabled: bool = False


class ShotDetector:
    """Detects and classifies shots in broadcast football video."""
    
    def __init__(self, fps: float = 25.0):
        self.fps = fps
        
        # Shot detection thresholds
        self.hard_cut_threshold = 0.35  # Normalized frame difference for hard cuts
        self.gradual_transition_threshold = 0.15  # Lower threshold for gradual changes
        self.min_shot_frames = int(0.5 * fps)  # Minimum 0.5 seconds per shot
        
        # Classification thresholds
        self.wide_green_ratio = 0.35  # High green ratio = wide shot
        self.close_up_edge_ratio = 0.15  # High edge density = close-up
        self.stadium_green_ratio = 0.05  # Very low green = stadium/crowd
        
    def detect_shots(self, frames: List[np.ndarray]) -> List[Shot]:
        """
        Detect shot boundaries and classify each shot.
        
        Args:
            frames: List of video frames (BGR format)
            
        Returns:
            List of Shot objects with boundaries and classifications
        """
        n_frames = len(frames)
        if n_frames == 0:
            return []
        
        print(f"Detecting shots in {n_frames} frames...")
        
        # Step 1: Detect boundaries
        boundaries = self._detect_boundaries(frames)
        print(f"  Found {len(boundaries)} shot boundaries")
        
        # Step 2: Create shot segments
        shots = self._create_shots(frames, boundaries)
        print(f"  Created {len(shots)} shots")
        
        # Step 3: Classify each shot
        for shot in shots:
            self._classify_shot(frames, shot)
        
        # Print summary
        type_counts = {}
        for shot in shots:
            type_counts[shot.shot_type.value] = type_counts.get(shot.shot_type.value, 0) + 1
        print(f"  Shot classification: {type_counts}")
        
        return shots
    
    def _detect_boundaries(self, frames: List[np.ndarray]) -> List[Tuple[int, TransitionType]]:
        """
        Detect shot boundaries using frame difference and histogram comparison.
        
        Returns:
            List of (frame_index, transition_type) tuples
        """
        n_frames = len(frames)
        boundaries = [(0, TransitionType.CONTINUOUS)]  # Start is always a boundary
        
        # Compute frame differences
        prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        prev_hist = cv2.calcHist([frames[0]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()
        
        diff_history = []
        
        for i in range(1, n_frames):
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            curr_hist = cv2.calcHist([frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            curr_hist = cv2.normalize(curr_hist, curr_hist).flatten()
            
            # Frame difference
            frame_diff = cv2.absdiff(prev_gray, curr_gray)
            diff_ratio = np.mean(frame_diff) / 255.0
            
            # Histogram difference
            hist_diff = 1.0 - cv2.compareHist(prev_hist, curr_hist, cv2.HISTCMP_CORREL)
            
            # Combined metric
            combined_diff = 0.6 * diff_ratio + 0.4 * hist_diff
            diff_history.append(combined_diff)
            
            # Detect cuts
            if combined_diff > self.hard_cut_threshold:
                # Hard cut detected
                if len(boundaries) == 0 or i - boundaries[-1][0] >= self.min_shot_frames:
                    boundaries.append((i, TransitionType.HARD_CUT))
            elif len(diff_history) >= 5:
                # Check for gradual transition (sustained elevated difference)
                recent_avg = np.mean(diff_history[-5:])
                if recent_avg > self.gradual_transition_threshold:
                    if len(boundaries) == 0 or i - boundaries[-1][0] >= self.min_shot_frames:
                        boundaries.append((i, TransitionType.GRADUAL))
                        diff_history = []  # Reset after detecting transition
            
            prev_gray = curr_gray
            prev_hist = curr_hist
        
        return boundaries
    
    def _create_shots(self, frames: List[np.ndarray], boundaries: List[Tuple[int, TransitionType]]) -> List[Shot]:
        """Create Shot objects from boundary detections."""
        shots = []
        n_frames = len(frames)
        
        for i in range(len(boundaries)):
            start_frame = boundaries[i][0]
            end_frame = boundaries[i + 1][0] - 1 if i + 1 < len(boundaries) else n_frames - 1
            
            # Skip very short shots
            if end_frame - start_frame < self.min_shot_frames:
                continue
            
            transition_in = boundaries[i][1]
            transition_out = boundaries[i + 1][1] if i + 1 < len(boundaries) else None
            
            shot = Shot(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=start_frame / self.fps,
                end_time=end_frame / self.fps,
                shot_type=ShotType.UNCERTAIN,
                confidence=0.0,
                transition_in=transition_in,
                transition_out=transition_out,
                green_ratio=0.0,
                edge_density=0.0,
                motion_level=0.0,
            )
            
            shots.append(shot)
        
        return shots
    
    def _classify_shot(self, frames: List[np.ndarray], shot: Shot):
        """
        Classify a shot based on visual features.
        
        Updates shot.shot_type and shot.confidence in-place.
        """
        # Sample frames from the shot (not too many to avoid slowdown)
        sample_indices = self._get_sample_indices(shot.start_frame, shot.end_frame, max_samples=5)
        
        green_ratios = []
        edge_densities = []
        motion_levels = []
        
        for i, frame_idx in enumerate(sample_indices):
            frame = frames[frame_idx]
            
            # Compute green ratio (pitch visibility)
            green_ratio = self._compute_green_ratio(frame)
            green_ratios.append(green_ratio)
            
            # Compute edge density
            edge_density = self._compute_edge_density(frame)
            edge_densities.append(edge_density)
            
            # Compute motion (if not first frame)
            if i > 0:
                prev_frame = frames[sample_indices[i - 1]]
                motion = self._compute_motion(prev_frame, frame)
                motion_levels.append(motion)
        
        # Aggregate features
        shot.green_ratio = float(np.mean(green_ratios))
        shot.edge_density = float(np.mean(edge_densities))
        shot.motion_level = float(np.mean(motion_levels)) if motion_levels else 0.0
        
        # Classification logic with explicit confidence scoring
        confidence_scores = {}
        
        # Wide tactical shot: High green ratio, moderate motion
        if shot.green_ratio > self.wide_green_ratio and shot.edge_density < 0.10:
            confidence_scores[ShotType.WIDE_TACTICAL] = 0.6 + 0.3 * (shot.green_ratio - self.wide_green_ratio) / (1.0 - self.wide_green_ratio)
        
        # Medium gameplay: Moderate green, moderate edge
        if 0.15 < shot.green_ratio < self.wide_green_ratio and shot.edge_density < 0.12:
            confidence_scores[ShotType.MEDIUM_GAMEPLAY] = 0.5 + 0.2 * shot.green_ratio
        
        # Close-up: High edge density, low/moderate green
        if shot.edge_density > self.close_up_edge_ratio and shot.green_ratio < 0.25:
            confidence_scores[ShotType.CLOSE_UP] = 0.5 + 0.4 * (shot.edge_density - self.close_up_edge_ratio)
        
        # Stadium/crowd: Very low green, low motion
        if shot.green_ratio < self.stadium_green_ratio and shot.motion_level < 0.02:
            confidence_scores[ShotType.STADIUM] = 0.6
        
        # Replay detection: Look for watermarks, slow motion patterns
        # (simplified - would need more sophisticated detection)
        if shot.motion_level < 0.01 and shot.green_ratio > 0.1:
            confidence_scores[ShotType.REPLAY] = 0.3  # Low confidence without better indicators
        
        # Select best classification
        if confidence_scores:
            shot.shot_type = max(confidence_scores, key=confidence_scores.get)
            shot.confidence = confidence_scores[shot.shot_type]
        else:
            shot.shot_type = ShotType.UNCERTAIN
            shot.confidence = 0.0
        
        # Set validity flags based on shot type
        if shot.shot_type in (ShotType.WIDE_TACTICAL, ShotType.MEDIUM_GAMEPLAY):
            shot.pitch_calibration_valid = shot.green_ratio > 0.20
            shot.camera_motion_valid = True
            shot.metrics_enabled = shot.pitch_calibration_valid
        else:
            shot.pitch_calibration_valid = False
            shot.camera_motion_valid = False
            shot.metrics_enabled = False
    
    def _get_sample_indices(self, start: int, end: int, max_samples: int = 5) -> List[int]:
        """Get evenly spaced sample frame indices."""
        shot_length = end - start + 1
        if shot_length <= max_samples:
            return list(range(start, end + 1))
        
        step = shot_length / max_samples
        return [start + int(i * step) for i in range(max_samples)]
    
    def _compute_green_ratio(self, frame: np.ndarray) -> float:
        """
        Compute ratio of green pixels (grass/pitch).
        
        Returns value between 0.0 and 1.0.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Green range for grass/pitch
        lower_green = np.array([32, 35, 35])
        upper_green = np.array([90, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        
        return green_pixels / total_pixels
    
    def _compute_edge_density(self, frame: np.ndarray) -> float:
        """
        Compute edge density using Canny edge detection.
        
        High values indicate detailed/close-up shots.
        Returns value between 0.0 and 1.0.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        
        return edge_pixels / total_pixels
    
    def _compute_motion(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        Compute motion between consecutive frames.
        
        Returns normalized motion metric between 0.0 and 1.0.
        """
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(prev_gray, curr_gray)
        return np.mean(diff) / 255.0
    
    def shots_to_dict(self, shots: List[Shot]) -> List[dict]:
        """Convert shots to JSON-serializable format."""
        return [
            {
                "start_frame": shot.start_frame,
                "end_frame": shot.end_frame,
                "start_time": round(shot.start_time, 2),
                "end_time": round(shot.end_time, 2),
                "duration_s": round(shot.end_time - shot.start_time, 2),
                "shot_type": shot.shot_type.value,
                "confidence": round(shot.confidence, 3),
                "transition_in": shot.transition_in.value,
                "transition_out": shot.transition_out.value if shot.transition_out else None,
                "features": {
                    "green_ratio": round(shot.green_ratio, 3),
                    "edge_density": round(shot.edge_density, 3),
                    "motion_level": round(shot.motion_level, 3),
                },
                "validity": {
                    "pitch_calibration": shot.pitch_calibration_valid,
                    "camera_motion": shot.camera_motion_valid,
                    "metrics_enabled": shot.metrics_enabled,
                }
            }
            for shot in shots
        ]
