"""Auto-calibrate a pitch homography from the first frame's grass trapezoid.

The homography maps pixel coords to pitch-plane coords in the auto-calibrated
coordinate system.  Because player-height scale estimation is unreliable on
broadcast footage, all positions are then rescaled to the real FIFA standard
pitch (105m × 68m) using a simple linear scale from auto-dims to real dims.
This ensures the minimap and speed calculations use physically correct units.
"""

import cv2
import numpy as np

from cv import config

# FIFA standard pitch dimensions used for ALL metric calculations.
# The auto-calibrated length_m / width_m are kept for internal homography use
# but the public transform_point() output is always in FIFA-standard metres.
FIFA_LENGTH = 105.0
FIFA_WIDTH  = 68.0


def _order_quad(pts):
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).ravel()
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([bl, tl, tr, br], dtype=np.float32)


def _field_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (32, 35, 35), (90, 255, 255))
    kernel = np.ones((15, 15), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if num <= 1:
        return mask
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    return np.uint8(labels == largest) * 255


def _quad_from_mask(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    cnt = max(contours, key=cv2.contourArea)
    if cv2.contourArea(cnt) < 0.08 * mask.shape[0] * mask.shape[1]:
        return None
    hull = cv2.convexHull(cnt)
    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, 0.02 * peri, True)
    if len(approx) >= 4:
        pts = approx.reshape(-1, 2).astype(np.float32)
        if len(pts) > 4:
            corners = cv2.boxPoints(cv2.minAreaRect(pts))
            pts = corners
        return _order_quad(pts)
    corners = cv2.boxPoints(cv2.minAreaRect(hull.reshape(-1, 2).astype(np.float32)))
    return _order_quad(corners)


def _player_scale(player_tracks_frame, quad):
    heights = []
    if not player_tracks_frame:
        return None
    ys = [quad[0][1], quad[3][1]]
    near_y = max(ys)
    for info in player_tracks_frame.values():
        bbox = info.get("bbox")
        if not bbox:
            continue
        h = bbox[3] - bbox[1]
        if h < 20:
            continue
        if bbox[3] < near_y * 0.45:
            continue
        heights.append(h)
    if len(heights) < 3:
        return None
    return config.PLAYER_HEIGHT_M / float(np.median(heights))


class PitchMapper:
    def __init__(self, frame, player_tracks_frame=None):
        # auto-calibrated dims (used only for internal homography)
        self._auto_length_m = config.PITCH_LENGTH
        self._auto_width_m  = config.PITCH_WIDTH
        # Public dims are always FIFA standard
        self.length_m = FIFA_LENGTH
        self.width_m  = FIFA_WIDTH
        self.pixel_vertices = None
        self.H = None
        self.ok = False
        self._fit(frame, player_tracks_frame)

    def _fallback_quad(self, frame):
        h, w = frame.shape[:2]
        return np.array(
            [[int(0.02 * w), h - 8], [int(0.18 * w), int(0.28 * h)], [int(0.88 * w), int(0.28 * h)], [int(0.98 * w), h - 8]],
            dtype=np.float32,
        )

    def _fit(self, frame, player_tracks_frame):
        """
        Fit homography directly from pixel quad to FIFA standard pitch coords.

        The pixel quad detected from the grass mask represents the visible
        pitch area.  For a broadcast wide-angle shot, the full pitch is
        visible, so we map the quad corners directly to the four corners of
        the 105m × 68m FIFA pitch.

        This avoids the intermediate auto-calibrated scale step which
        introduced systematic errors (auto_length was ~50m, auto_width ~30m
        instead of 105×68).
        """
        mask = _field_mask(frame)
        quad = _quad_from_mask(mask)
        if quad is None:
            quad = self._fallback_quad(frame)

        self.pixel_vertices = quad

        # Pixel quad order from _order_quad: [BL, TL, TR, BR]
        # Map directly to FIFA pitch corners:
        #   BL → (0,    FIFA_WIDTH)   bottom-left
        #   TL → (0,    0)            top-left
        #   TR → (FIFA_LENGTH, 0)     top-right
        #   BR → (FIFA_LENGTH, FIFA_WIDTH) bottom-right
        target = np.array(
            [
                [0.0,        FIFA_WIDTH ],   # BL
                [0.0,        0.0        ],   # TL
                [FIFA_LENGTH, 0.0       ],   # TR
                [FIFA_LENGTH, FIFA_WIDTH],   # BR
            ],
            dtype=np.float32,
        )
        self.H  = cv2.getPerspectiveTransform(quad, target)
        self.ok = True

        # Store auto dims for compatibility (validation code checks these)
        self._auto_length_m = FIFA_LENGTH
        self._auto_width_m  = FIFA_WIDTH

    def transform_point(self, point):
        """
        Transform a pixel point directly to FIFA-standard pitch coordinates (metres).

        The homography was fitted mapping pixel quad corners → FIFA pitch corners
        (0-105m × 0-68m), so no additional rescaling is needed.
        """
        if self.H is None or point is None:
            return None
        pt  = np.array(point, dtype=np.float32).reshape(-1, 1, 2)
        out = cv2.perspectiveTransform(pt, self.H).reshape(-1, 2)[0]
        x, y = float(out[0]), float(out[1])

        # Reject degenerate or out-of-pitch results instead of snapping them
        # onto a boundary, which would create misleading minimap positions.
        if not np.isfinite(x) or not np.isfinite(y):
            return None
        tolerance = 1e-3
        if (
            x < -tolerance
            or x > FIFA_LENGTH + tolerance
            or y < -tolerance
            or y > FIFA_WIDTH + tolerance
        ):
            return None

        return [round(x, 2), round(y, 2)]


def add_transformed_positions(tracks, mapper):
    for object_tracks in tracks.values():
        for frame_num, track in enumerate(object_tracks):
            for track_id, track_info in track.items():
                position = track_info.get("position_adjusted", track_info.get("position"))
                track_info["position_transformed"] = mapper.transform_point(position)
