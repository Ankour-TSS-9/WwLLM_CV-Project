"""
Shot-aware pitch calibration.

Fits pitch homography separately for each appropriate shot and
validates calibration quality.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional
from cv.shot_detector import Shot, ShotType
from cv.pitch import PitchMapper
from cv import config


class ShotAwarePitchMapper:
    """Pitch mapper that respects shot boundaries and validates calibrations."""
    
    def __init__(self, shots: List[Shot]):
        self.shots = shots
        self.shot_mappers = {}  # shot_index -> PitchMapper
        self.calibration_frames = {}  # shot_index -> frame used to fit its homography
        self.shot_lookup = self._build_shot_lookup(shots)
        # Default dimensions for compatibility
        self.length_m = config.PITCH_LENGTH
        self.width_m = config.PITCH_WIDTH
    
    def _build_shot_lookup(self, shots: List[Shot]) -> Dict[int, int]:
        """Build frame -> shot_index lookup."""
        lookup = {}
        for idx, shot in enumerate(shots):
            for frame in range(shot.start_frame, shot.end_frame + 1):
                lookup[frame] = idx
        return lookup
    
    def fit_shots(self, frames: List[np.ndarray], tracks: dict):
        """
        Fit pitch calibration for each appropriate shot.
        
        Args:
            frames: All video frames
            tracks: Player tracking data
        """
        print("Fitting pitch calibrations per shot...")
        
        valid_count = 0
        for idx, shot in enumerate(self.shots):
            if not shot.pitch_calibration_valid:
                # Skip shots that aren't suitable for calibration
                continue
            
            # Use middle frame of shot for calibration
            mid_frame = (shot.start_frame + shot.end_frame) // 2
            frame = frames[mid_frame]
            
            # Get player tracks for this frame
            player_tracks_frame = {}
            for key in ("players", "goalkeepers"):
                if key in tracks and mid_frame < len(tracks[key]):
                    player_tracks_frame.update(tracks[key][mid_frame])
            
            # Fit pitch mapper
            mapper = PitchMapper(frame, player_tracks_frame)
            
            # Validate calibration quality
            if self._validate_calibration(mapper, shot):
                self.shot_mappers[idx] = mapper
                self.calibration_frames[idx] = mid_frame
                valid_count += 1
                shot.pitch_calibration_valid = True
                shot.metrics_enabled = True
                # Update representative dimensions from first valid shot
                if valid_count == 1:
                    self.length_m = mapper.length_m
                    self.width_m = mapper.width_m
            else:
                shot.pitch_calibration_valid = False
                shot.metrics_enabled = False
        
        print(f"  Valid pitch calibrations: {valid_count}/{len(self.shots)}")
    
    def _validate_calibration(self, mapper: PitchMapper, shot: Shot) -> bool:
        """
        Validate pitch calibration quality.
        
        Checks if the calibration is reasonable for metric computation.
        """
        if not mapper.ok:
            return False
        
        # Check homography matrix exists and is well-conditioned
        if mapper.H is None:
            return False
        
        try:
            cond = np.linalg.cond(mapper.H)
            if cond > 1e10:  # Ill-conditioned matrix
                return False
        except:
            return False
        
        # Check pitch dimensions are reasonable
        # PitchMapper.length_m / width_m are now always FIFA standard (105/68)
        # so the check is always true — validate using internal auto dims instead
        if mapper._auto_length_m < 20 or mapper._auto_length_m > 130:
            return False
        if mapper._auto_width_m < 15 or mapper._auto_width_m > 90:
            return False
        
        # Check if green ratio is sufficient
        if shot.green_ratio < 0.15:
            return False
        
        # Check if we have enough corner points
        if mapper.pixel_vertices is None:
            return False
        
        # Check if quadrilateral is reasonable (not too distorted)
        quad = mapper.pixel_vertices
        areas = []
        for i in range(4):
            p1 = quad[i]
            p2 = quad[(i + 1) % 4]
            p3 = quad[(i + 2) % 4]
            # Triangle area
            area = abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (p2[1] - p1[1])) / 2
            areas.append(area)
        
        # If triangles have very different areas, quad is too distorted
        if max(areas) > 3 * min(areas) if min(areas) > 0 else True:
            return False
        
        return True
    
    def transform_point(self, point, frame_num: int) -> Optional[list]:
        """
        Transform a point using shot-appropriate calibration.
        
        Args:
            point: (x, y) pixel coordinates
            frame_num: Frame number
            
        Returns:
            [x, y] in meters, or None if no valid calibration
        """
        shot_idx = self.shot_lookup.get(frame_num)
        if shot_idx is None:
            return None
        
        mapper = self.shot_mappers.get(shot_idx)
        if mapper is None:
            return None
        
        return mapper.transform_point(point)
    
    def add_transformed_positions(self, tracks: dict, camera_data: Optional[dict] = None):
        """
        Add transformed positions to tracks with shot-aware validity.
        
        Only transforms positions when calibration is valid for that shot.
        """
        for object_tracks in tracks.values():
            for frame_num, track in enumerate(object_tracks):
                shot_idx = self.shot_lookup.get(frame_num)
                shot = self.shots[shot_idx] if shot_idx is not None else None
                mapper = self.shot_mappers.get(shot_idx) if shot_idx is not None else None
                
                for track_id, track_info in track.items():
                    position = track_info.get("position")
                    if (
                        position is not None
                        and camera_data is not None
                        and mapper is not None
                        and shot_idx in self.calibration_frames
                    ):
                        calibration_frame = self.calibration_frames[shot_idx]
                        valid = camera_data.get("valid", [])
                        cumulative = camera_data.get("cumulative", [])
                        if (
                            frame_num < len(valid)
                            and calibration_frame < len(valid)
                            and valid[frame_num]
                            and valid[calibration_frame]
                            and frame_num < len(cumulative)
                            and calibration_frame < len(cumulative)
                        ):
                            # The homography is fitted in midpoint-frame pixels.
                            # Shift the current footpoint into that same frame.
                            current_adjusted = track_info.get("position_adjusted", position)
                            position = (
                                current_adjusted[0] + cumulative[calibration_frame][0],
                                current_adjusted[1] + cumulative[calibration_frame][1],
                            )

                    if mapper is not None and shot and shot.metrics_enabled:
                        # Valid calibration exists
                        transformed = mapper.transform_point(position)
                        track_info["position_transformed"] = transformed
                        track_info["pitch_valid"] = transformed is not None
                    else:
                        # No valid calibration
                        track_info["position_transformed"] = None
                        track_info["pitch_valid"] = False
    
    def get_mapper_for_frame(self, frame_num: int) -> Optional[PitchMapper]:
        """Get the pitch mapper for a specific frame, if valid."""
        shot_idx = self.shot_lookup.get(frame_num)
        if shot_idx is None:
            return None
        return self.shot_mappers.get(shot_idx)
    
    def get_pitch_dimensions(self, frame_num: int) -> tuple:
        """Get pitch dimensions for a frame, or defaults if invalid."""
        mapper = self.get_mapper_for_frame(frame_num)
        if mapper:
            return mapper.length_m, mapper.width_m
        return config.PITCH_LENGTH, config.PITCH_WIDTH
