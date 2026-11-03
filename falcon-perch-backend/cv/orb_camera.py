"""
Phase E1 — Experimental ORB Global Motion Compensation (GMC)

Drop-in replacement for ImprovedCameraEstimator that uses ORB feature
matching and RANSAC-based affine estimation instead of Lucas-Kanade median
flow.

Interface contract:
  - Same constructor signature as ImprovedCameraEstimator(frame).
  - Same _exclusion_mask(frame, tracks, frame_num) method (used by
    ShotAwareCameraEstimator directly via self.base_estimator._exclusion_mask).
  - get_camera_movement returns the same {delta, cumulative} dict.
  - add_adjust_positions_to_tracks mirrors the base class exactly.

Feature flag:
  Set USE_ORB_GMC = True in run_cv_shot_aware.py (or pass --orb-gmc flag)
  to activate.  The default Lucas-Kanade path is preserved and unchanged.

Do NOT edit this to replace the baseline. This is an experiment module only.
"""

import os
import pickle
import time

import cv2
import numpy as np

from cv import config


class ORBCameraEstimator:
    """
    ORB-based Global Motion Compensation.

    Algorithm:
      1. Detect ORB keypoints on both consecutive frames, applying an
         exclusion mask that blanks out player/ball bounding boxes so
         player motion does not contaminate the camera estimate.
      2. Match descriptors with a Brute-Force Hamming matcher (cross-check).
      3. Estimate a partial-affine transform (rotation + scale + translation)
         with RANSAC via cv2.estimateAffinePartial2D.  Partial affine is
         chosen over full homography to avoid degenerate solutions on
         near-planar pitch backgrounds.
      4. Extract (tx, ty) translation from the 2×3 affine matrix.
      5. Accumulate translations across frames to form the cumulative array.

    Why partial-affine and not homography:
      Broadcast football cameras pan and tilt; zoom is rare and small.
      A 4-DOF partial affine (rotation + isotropic scale + translation)
      captures the dominant motion while being more numerically stable than
      an 8-DOF homography on a nearly-featureless pitch background.
    """

    # Config defaults (all overridable via cv/config.py keys)
    _ORB_FEATURES   = getattr(config, "ORB_MAX_FEATURES",   1200)
    _MATCH_RATIO    = getattr(config, "ORB_MATCH_RATIO",     0.8)   # not used (crossCheck)
    _MIN_INLIERS    = getattr(config, "ORB_MIN_INLIERS",     12)
    _MIN_MATCHES    = getattr(config, "ORB_MIN_MATCHES",     15)
    _TOP_MATCHES    = getattr(config, "ORB_TOP_MATCHES",     80)
    _MAX_DELTA_PX   = getattr(config, "ORB_MAX_DELTA_PX",   50.0)   # sanity clamp
    _MIN_DELTA_PX   = getattr(config, "ORB_MIN_DELTA_PX",    1.0)   # sub-pixel threshold
    _RANSAC_CONF    = getattr(config, "ORB_RANSAC_CONF",    0.995)
    _RANSAC_THRESH  = getattr(config, "ORB_RANSAC_THRESH",   3.0)

    def __init__(self, frame: np.ndarray):
        """
        Args:
            frame: The first video frame (BGR).  Used only to record shape.
        """
        self.frame_shape = frame.shape[:2]
        self.minimum_distance = 1.0   # kept for ShotAwareCameraEstimator compat

        self._orb = cv2.ORB_create(nfeatures=self._ORB_FEATURES)
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        # ---- compat attributes expected by ShotAwareCameraEstimator ----
        # ShotAwareCameraEstimator._compute_shot_motion reads these via
        # self.base_estimator.feature_params and self.base_estimator.lk_params
        # to drive its own LK-based inner loop.  We expose them so the shot-
        # aware wrapper continues to work when ORBCameraEstimator is used as
        # the base_estimator.  They are not used by ORBCameraEstimator itself.
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

    # ------------------------------------------------------------------
    # Public API (must match ImprovedCameraEstimator exactly)
    # ------------------------------------------------------------------

    def get_camera_movement(
        self,
        frames,
        tracks=None,
        read_from_stub: bool = False,
        stub_path: str | None = None,
    ) -> dict:
        """
        Compute per-frame camera motion using ORB GMC.

        Returns:
            {
              "delta":      [[dx, dy], ...],   # per-frame translation
              "cumulative": [[cx, cy], ...],   # accumulated from frame 0
              "method":     "orb_gmc",         # identifier for comparison
              "inlier_counts": [int, ...],     # RANSAC inliers per frame
              "match_counts":  [int, ...],     # raw match count per frame
              "failure_frames": [int, ...],    # frames where estimation failed
            }
        """
        if read_from_stub and stub_path and os.path.exists(stub_path):
            with open(stub_path, "rb") as f:
                return pickle.load(f)

        n = len(frames)
        deltas         = [[0.0, 0.0] for _ in range(n)]
        cumulative     = [[0.0, 0.0] for _ in range(n)]
        inlier_counts  = [0] * n
        match_counts   = [0] * n
        failure_frames = []

        prev_gray, prev_kps, prev_des = self._prepare_frame(frames[0], tracks, 0)

        for i in range(1, n):
            curr_gray, curr_kps, curr_des = self._prepare_frame(frames[i], tracks, i)

            dx, dy, n_inliers, n_matches = self._estimate_translation(
                prev_kps, prev_des, curr_kps, curr_des
            )

            if n_inliers < self._MIN_INLIERS:
                failure_frames.append(i)

            deltas[i] = [dx, dy]
            cumulative[i] = [
                cumulative[i - 1][0] + dx,
                cumulative[i - 1][1] + dy,
            ]
            inlier_counts[i] = n_inliers
            match_counts[i]  = n_matches

            prev_gray, prev_kps, prev_des = curr_gray, curr_kps, curr_des

        result = {
            "delta":         deltas,
            "cumulative":    cumulative,
            "method":        "orb_gmc",
            "inlier_counts": inlier_counts,
            "match_counts":  match_counts,
            "failure_frames": failure_frames,
        }

        if stub_path:
            os.makedirs(os.path.dirname(stub_path) or ".", exist_ok=True)
            with open(stub_path, "wb") as f:
                pickle.dump(result, f)

        return result

    def add_adjust_positions_to_tracks(self, tracks: dict, camera_cumulative: list):
        """
        Mirror of ImprovedCameraEstimator.add_adjust_positions_to_tracks.

        Args:
            tracks:           pipeline tracks dict
            camera_cumulative: camera["cumulative"]  (plain list of [cx, cy])
        """
        n_valid = len(camera_cumulative)
        for object_tracks in tracks.values():
            for frame_num, track in enumerate(object_tracks):
                if frame_num >= n_valid:
                    continue
                for track_info in track.values():
                    position = track_info.get("position")
                    if position is None:
                        continue
                    cam = camera_cumulative[frame_num]
                    track_info["position_adjusted"] = (
                        position[0] - cam[0],
                        position[1] - cam[1],
                    )

    def _exclusion_mask(self, frame: np.ndarray, tracks, frame_num: int) -> np.ndarray:
        """
        Identical to ImprovedCameraEstimator._exclusion_mask.

        Returns a uint8 mask (255 = usable background, 0 = player/ball region).
        Used by ShotAwareCameraEstimator via self.base_estimator._exclusion_mask.
        """
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_frame(self, frame: np.ndarray, tracks, frame_num: int):
        """Grayscale, mask, detect ORB keypoints and descriptors."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = self._exclusion_mask(frame, tracks, frame_num)
        kps, des = self._orb.detectAndCompute(gray, mask)
        return gray, kps, des

    def _estimate_translation(self, prev_kps, prev_des, curr_kps, curr_des):
        """
        Match descriptors, run RANSAC affine estimation, return (dx, dy, inliers, matches).

        Returns (0.0, 0.0, 0, 0) when estimation is unreliable.
        """
        if (prev_des is None or curr_des is None
                or len(prev_kps) < self._MIN_MATCHES
                or len(curr_kps) < self._MIN_MATCHES):
            return 0.0, 0.0, 0, 0

        matches = self._matcher.match(curr_des, prev_des)
        n_matches = len(matches)
        if n_matches < self._MIN_MATCHES:
            return 0.0, 0.0, 0, n_matches

        # Sort by descriptor distance and take the best N
        matches = sorted(matches, key=lambda m: m.distance)[: self._TOP_MATCHES]

        pts_curr = np.float32(
            [curr_kps[m.queryIdx].pt for m in matches]
        ).reshape(-1, 1, 2)
        pts_prev = np.float32(
            [prev_kps[m.trainIdx].pt for m in matches]
        ).reshape(-1, 1, 2)

        # Partial affine: 4-DOF (rotation + isotropic scale + translation).
        # Argument order: estimateAffinePartial2D(from, to) -> matrix that maps
        # "from" points to "to" points.  We pass (prev, curr) so the extracted
        # translation (tx, ty) represents how the scene moved forward in time,
        # i.e. the camera pan vector.  Passing (curr, prev) would give the
        # negated (inverse) translation.
        M, inliers = cv2.estimateAffinePartial2D(
            pts_prev,
            pts_curr,
            method=cv2.RANSAC,
            ransacReprojThreshold=self._RANSAC_THRESH,
            confidence=self._RANSAC_CONF,
        )
        n_inliers = int(np.sum(inliers)) if inliers is not None else 0

        if M is None or n_inliers < self._MIN_INLIERS:
            return 0.0, 0.0, n_inliers, n_matches

        # Translation is the last column of the 2×3 affine matrix
        # M = [[a, b, tx],
        #      [c, d, ty]]
        tx, ty = float(M[0, 2]), float(M[1, 2])

        # Sanity clamp: reject implausible jumps
        if abs(tx) > self._MAX_DELTA_PX or abs(ty) > self._MAX_DELTA_PX:
            return 0.0, 0.0, n_inliers, n_matches

        # Sub-pixel noise gate
        if abs(tx) < self._MIN_DELTA_PX and abs(ty) < self._MIN_DELTA_PX:
            tx, ty = 0.0, 0.0

        return tx, ty, n_inliers, n_matches

    # ------------------------------------------------------------------
    # Optional draw helper (mirrors ImprovedCameraEstimator.draw_camera_movement)
    # ------------------------------------------------------------------

    def draw_camera_movement(self, frames, camera: dict):
        """Draw cumulative camera shift and ORB diagnostics on each frame."""
        cumulative    = camera["cumulative"]
        inlier_counts = camera.get("inlier_counts", [0] * len(frames))
        failure_set   = set(camera.get("failure_frames", []))
        output_frames = []

        for i, frame in enumerate(frames):
            frame = frame.copy()
            overlay = frame.copy()
            colour = (200, 200, 200) if i not in failure_set else (180, 180, 255)
            cv2.rectangle(overlay, (0, 0), (560, 110), colour, -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            cx, cy = cumulative[i]
            text_col = (0, 80, 0) if i not in failure_set else (0, 0, 160)
            cv2.putText(frame, f"ORB GMC  X: {cx:.1f}  Y: {cy:.1f}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_col, 2)
            cv2.putText(frame, f"Inliers: {inlier_counts[i]}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, text_col, 2)
            if i in failure_set:
                cv2.putText(frame, "ESTIMATION FAILED",
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)
            output_frames.append(frame)

        return output_frames
