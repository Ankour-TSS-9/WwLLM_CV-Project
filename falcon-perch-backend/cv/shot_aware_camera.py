"""
Shot-aware camera motion estimation.

Resets camera state on shot boundaries and validates motion estimates
only within appropriate shot types.
"""

import numpy as np
import cv2
from typing import List, Optional, Dict
from cv.shot_detector import Shot, ShotType


class ShotAwareCameraEstimator:
    """Camera motion estimator that respects shot boundaries."""
    
    def __init__(self, base_estimator, shots: List[Shot]):
        """
        Args:
            base_estimator: Instance of ImprovedCameraEstimator
            shots: List of detected shots
        """
        self.base_estimator = base_estimator
        self.shots = shots
        self.shot_lookup = self._build_shot_lookup(shots)
    
    def _build_shot_lookup(self, shots: List[Shot]) -> Dict[int, int]:
        """Build frame -> shot_index lookup."""
        lookup = {}
        for idx, shot in enumerate(shots):
            for frame in range(shot.start_frame, shot.end_frame + 1):
                lookup[frame] = idx
        return lookup
    
    def get_camera_movement(self, frames, tracks=None) -> dict:
        """
        Compute camera movement with shot-aware resets.
        
        Returns:
            Dictionary with 'delta', 'cumulative', and 'valid' arrays
        """
        n = len(frames)
        deltas = [[0.0, 0.0] for _ in range(n)]
        cumulative = [[0.0, 0.0] for _ in range(n)]
        valid = [False] * n  # Track which frames have valid camera motion
        
        # Process each shot independently
        for shot in self.shots:
            if not shot.camera_motion_valid:
                # Skip camera motion for close-ups, stadium shots, etc.
                continue
            
            # Get shot frames
            start = shot.start_frame
            end = min(shot.end_frame + 1, n)
            shot_frames = frames[start:end]
            
            if len(shot_frames) < 2:
                continue
            
            # Compute motion within this shot
            shot_deltas, shot_cumulative = self._compute_shot_motion(
                shot_frames, tracks, start
            )
            
            # Store results
            for i, frame_idx in enumerate(range(start, end)):
                if i < len(shot_deltas):
                    deltas[frame_idx] = shot_deltas[i]
                    cumulative[frame_idx] = shot_cumulative[i]
                    valid[frame_idx] = True
        
        return {
            "delta": deltas,
            "cumulative": cumulative,
            "valid": valid,
            "shots": self.shots
        }
    
    def _compute_shot_motion(self, frames, tracks, offset: int):
        """Compute camera motion for a single shot."""
        n = len(frames)
        deltas = [[0.0, 0.0] for _ in range(n)]
        cumulative = [[0.0, 0.0] for _ in range(n)]
        
        old_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        mask = self.base_estimator._exclusion_mask(frames[0], tracks, offset)
        old_features = cv2.goodFeaturesToTrack(old_gray, mask=mask, **self.base_estimator.feature_params)
        
        for i in range(1, n):
            frame_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            dx, dy = 0.0, 0.0
            
            if old_features is not None and len(old_features) >= 8:
                new_features, status, _ = cv2.calcOpticalFlowPyrLK(
                    old_gray, frame_gray, old_features, None, **self.base_estimator.lk_params
                )
                if new_features is not None and status is not None:
                    good_new = new_features[status.flatten() == 1]
                    good_old = old_features[status.flatten() == 1]
                    
                    if len(good_new) >= 8:
                        flows = good_new.reshape(-1, 2) - good_old.reshape(-1, 2)
                        
                        # Robust outlier rejection using MAD (Median Absolute Deviation)
                        median_flow = np.median(flows, axis=0)
                        deviations = np.abs(flows - median_flow)
                        mad = np.median(deviations, axis=0)
                        
                        # Keep only inliers (within 2.5 MAD of median)
                        threshold = 2.5 * mad
                        inliers = np.all(deviations < threshold + 1e-6, axis=1)
                        
                        if np.sum(inliers) >= 5:
                            flows_clean = flows[inliers]
                            dx = float(np.median(flows_clean[:, 0]))
                            dy = float(np.median(flows_clean[:, 1]))
                            
                            # Additional sanity check: reject unreasonable motion
                            if abs(dx) > 50 or abs(dy) > 50:
                                dx, dy = 0.0, 0.0
                            elif abs(dx) < self.base_estimator.minimum_distance and abs(dy) < self.base_estimator.minimum_distance:
                                dx, dy = 0.0, 0.0
            
            deltas[i] = [dx, dy]
            cumulative[i] = [
                cumulative[i - 1][0] + dx,
                cumulative[i - 1][1] + dy,
            ]
            
            mask = self.base_estimator._exclusion_mask(frames[i], tracks, offset + i)
            old_features = cv2.goodFeaturesToTrack(frame_gray, mask=mask, **self.base_estimator.feature_params)
            old_gray = frame_gray
        
        return deltas, cumulative
    
    def add_adjust_positions_to_tracks(self, tracks, camera_data):
        """
        Add adjusted positions with shot-aware validity.

        Only adjusts positions when camera motion is valid.
        Guards against stale stubs whose frame count exceeds the current video.
        """
        valid = camera_data["valid"]
        cumulative = camera_data["cumulative"]
        n_valid = len(valid)

        for object_tracks in tracks.values():
            for frame_num, track in enumerate(object_tracks):
                # Skip frames beyond what the camera estimator covered.
                # This can happen when a cached tracks stub was produced from a
                # longer video than the one being processed right now.
                if frame_num >= n_valid:
                    continue

                for track_id, track_info in track.items():
                    position = track_info.get("position")
                    if position is None:
                        continue

                    if valid[frame_num]:
                        # Valid camera motion - apply adjustment
                        cam = cumulative[frame_num]
                        track_info["position_adjusted"] = (
                            position[0] - cam[0],
                            position[1] - cam[1],
                        )
                        track_info["camera_valid"] = True
                    else:
                        # Invalid camera motion - keep original position
                        track_info["position_adjusted"] = position
                        track_info["camera_valid"] = False
    
    def draw_camera_movement(self, frames, camera_data):
        """Camera overlay removed — no longer drawn on video output."""
        return frames
