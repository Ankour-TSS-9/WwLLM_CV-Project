import os
import pickle
import sys

import cv2
import numpy as np

sys.path.append("../")


class ImprovedCameraEstimator:
    """Background optical flow, median vector, accumulated from frame 0."""

    def __init__(self, frame):
        self.lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        self.feature_params = dict(
            maxCorners=200,
            qualityLevel=0.1,
            minDistance=7,
            blockSize=7,
        )
        self.minimum_distance = 1.0
        self.frame_shape = frame.shape[:2]

    def _exclusion_mask(self, frame, tracks, frame_num):
        mask = np.ones(frame.shape[:2], dtype=np.uint8) * 255
        if tracks is None:
            return mask
        for key in ("players", "goalkeepers", "referees", "ball"):
            frame_tracks = tracks.get(key, [])
            if frame_num >= len(frame_tracks):
                continue
            for info in frame_tracks[frame_num].values():
                bbox = info.get("bbox")
                if not bbox:
                    continue
                x1, y1, x2, y2 = [int(v) for v in bbox]
                pad = 8
                y1 = max(0, y1 - pad)
                x1 = max(0, x1 - pad)
                y2 = min(mask.shape[0], y2 + pad)
                x2 = min(mask.shape[1], x2 + pad)
                mask[y1:y2, x1:x2] = 0
        return mask

    def add_adjust_positions_to_tracks(self, tracks, camera_cumulative):
        for object_tracks in tracks.values():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    position = track_info.get("position")
                    if position is None:
                        continue
                    cam = camera_cumulative[frame_num]
                    track_info["position_adjusted"] = (
                        position[0] - cam[0],
                        position[1] - cam[1],
                    )

    def get_camera_movement(self, frames, tracks=None, read_from_stub=False, stub_path=None):
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, "rb") as f:
                return pickle.load(f)

        n = len(frames)
        deltas = [[0.0, 0.0] for _ in range(n)]
        cumulative = [[0.0, 0.0] for _ in range(n)]

        old_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        mask = self._exclusion_mask(frames[0], tracks, 0)
        old_features = cv2.goodFeaturesToTrack(old_gray, mask=mask, **self.feature_params)

        for frame_num in range(1, n):
            frame_gray = cv2.cvtColor(frames[frame_num], cv2.COLOR_BGR2GRAY)
            dx, dy = 0.0, 0.0

            if old_features is not None and len(old_features) >= 8:
                new_features, status, _ = cv2.calcOpticalFlowPyrLK(
                    old_gray, frame_gray, old_features, None, **self.lk_params
                )
                if new_features is not None and status is not None:
                    good_new = new_features[status.flatten() == 1]
                    good_old = old_features[status.flatten() == 1]
                    if len(good_new) >= 8:
                        flows = good_new.reshape(-1, 2) - good_old.reshape(-1, 2)
                        dx = float(np.median(flows[:, 0]))
                        dy = float(np.median(flows[:, 1]))
                        if abs(dx) < self.minimum_distance and abs(dy) < self.minimum_distance:
                            dx, dy = 0.0, 0.0

            deltas[frame_num] = [dx, dy]
            cumulative[frame_num] = [
                cumulative[frame_num - 1][0] + dx,
                cumulative[frame_num - 1][1] + dy,
            ]

            mask = self._exclusion_mask(frames[frame_num], tracks, frame_num)
            old_features = cv2.goodFeaturesToTrack(frame_gray, mask=mask, **self.feature_params)
            old_gray = frame_gray

        result = {"delta": deltas, "cumulative": cumulative}
        if stub_path is not None:
            os.makedirs(os.path.dirname(stub_path) or ".", exist_ok=True)
            with open(stub_path, "wb") as f:
                pickle.dump(result, f)
        return result

    def draw_camera_movement(self, frames, camera):
        """Camera overlay removed — no longer drawn on video output."""
        return frames
