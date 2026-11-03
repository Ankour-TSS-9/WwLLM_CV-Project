import sys

import cv2

sys.path.append("../")
from utils import measure_distance, get_foot_position

from cv import config


class ImprovedSpeedEstimator:
    def __init__(self, fps):
        self.frame_window = config.SPEED_FRAME_WINDOW
        self.frame_rate = fps if fps and fps > 1 else 24.0

    def add_speed_and_distance_to_tracks(self, tracks):
        total_distance = {}

        for object_name, object_tracks in tracks.items():
            if object_name in ("ball", "referees"):
                continue
            n = len(object_tracks)
            for frame_num in range(0, n, self.frame_window):
                last_frame = min(frame_num + self.frame_window, n - 1)
                if last_frame == frame_num:
                    continue
                for track_id in object_tracks[frame_num]:
                    if track_id not in object_tracks[last_frame]:
                        continue
                    start = object_tracks[frame_num][track_id].get("position_transformed")
                    end = object_tracks[last_frame][track_id].get("position_transformed")
                    if start is None or end is None:
                        continue

                    distance_covered = measure_distance(start, end)
                    time_elapsed = (last_frame - frame_num) / self.frame_rate
                    if time_elapsed <= 0:
                        continue
                    speed_kmh = (distance_covered / time_elapsed) * 3.6
                    if speed_kmh > config.MAX_PLAYER_KMH:
                        continue
                    if distance_covered > config.MAX_STEP_M * (last_frame - frame_num):
                        continue

                    total_distance.setdefault(object_name, {})
                    total_distance[object_name][track_id] = (
                        total_distance[object_name].get(track_id, 0) + distance_covered
                    )

                    for f in range(frame_num, last_frame):
                        if track_id not in tracks[object_name][f]:
                            continue
                        tracks[object_name][f][track_id]["speed"] = speed_kmh
                        tracks[object_name][f][track_id]["distance"] = total_distance[object_name][
                            track_id
                        ]

        self._ball_speed(tracks)

    def _ball_speed(self, tracks):
        ball_frames = tracks.get("ball", [])
        prev = None
        prev_i = None
        for i, frame_ball in enumerate(ball_frames):
            info = frame_ball.get(1)
            if not info:
                continue
            pos = info.get("position_transformed")
            if pos is None:
                continue
            if prev is not None:
                dt = (i - prev_i) / self.frame_rate
                if dt > 0:
                    mps = measure_distance(prev, pos) / dt
                    speed_kmh = mps * 3.6
                    if speed_kmh <= config.MAX_BALL_KMH:
                        info["speed"] = speed_kmh
            prev = pos
            prev_i = i

    def draw_speed_and_distance(self, frames, tracks):
        output_frames = []
        for frame_num, frame in enumerate(frames):
            for object_name, object_tracks in tracks.items():
                if object_name in ("ball", "referees"):
                    continue
                if frame_num >= len(object_tracks):
                    continue
                for _, track_info in object_tracks[frame_num].items():
                    speed = track_info.get("speed")
                    distance = track_info.get("distance")
                    if speed is None or distance is None:
                        continue
                    position = list(get_foot_position(track_info["bbox"]))
                    position[1] += 40
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
