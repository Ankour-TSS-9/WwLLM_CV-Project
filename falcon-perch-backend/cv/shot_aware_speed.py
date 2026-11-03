"""
Shot-aware speed and distance overlay.

Only displays speed/distance when pitch calibration is valid and values are physically realistic.
"""

import cv2
from typing import List
from cv.shot_detector import Shot
from cv import config
from utils import get_foot_position


def draw_speed_and_distance_conditional(frames, tracks, shots: List[Shot]):
    """
    Draw speed and distance labels only when metrics are valid and realistic.
    
    Args:
        frames: Video frames
        tracks: Tracking data
        shots: List of Shot objects with validity flags
    """
    output_frames = []
    
    # Build shot lookup
    shot_lookup = {}
    for idx, shot in enumerate(shots):
        for frame in range(shot.start_frame, shot.end_frame + 1):
            shot_lookup[frame] = idx
    
    # Sanity check thresholds
    MAX_SPEED = config.MAX_PLAYER_KMH  # 36 km/h
    MAX_DISTANCE = 200.0  # meters (reasonable for a single tracking session)
    
    for frame_num, frame in enumerate(frames):
        # Check if metrics are enabled for this frame
        shot_idx = shot_lookup.get(frame_num)
        shot = shots[shot_idx] if shot_idx is not None else None
        metrics_valid = shot.metrics_enabled if shot else False
        
        # Only draw speed/distance if metrics valid
        if metrics_valid:
            for object_name, object_tracks in tracks.items():
                if object_name in ("ball", "referees"):
                    continue
                if frame_num >= len(object_tracks):
                    continue
                for _, track_info in object_tracks[frame_num].items():
                    # Check if this specific player has valid pitch mapping
                    if not track_info.get("pitch_valid", False):
                        continue
                    
                    speed = track_info.get("speed")
                    distance = track_info.get("distance")
                    if speed is None or distance is None:
                        continue
                    
                    # SANITY CHECK: Skip physically impossible values
                    if speed < 0 or speed > MAX_SPEED:
                        continue
                    if distance < 0 or distance > MAX_DISTANCE:
                        continue
                    
                    # Increased spacing from player ID label (was 40, now 55)
                    position = list(get_foot_position(track_info["bbox"]))
                    position[1] += 55
                    position = tuple(map(int, position))
                    
                    cv2.putText(
                        frame,
                        f"{speed:.1f} km/h",
                        position,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 0),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"{distance:.1f} m",
                        (position[0], position[1] + 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 0),
                        2,
                    )
        
        output_frames.append(frame)
    
    return output_frames
