"""
Shot-aware video annotation that respects shot validity.

Only displays metrics when they are valid for the current shot.
"""

import cv2
import numpy as np
from typing import List, Optional, Dict
from cv.shot_detector import Shot, ShotType


def draw_ellipse(frame, bbox, color, track_id=None):
    """Draw player ellipse and ID."""
    from utils import get_center_of_bbox, get_bbox_width
    
    y2 = int(bbox[3])
    x_center, _ = get_center_of_bbox(bbox)
    width = get_bbox_width(bbox)
    cv2.ellipse(
        frame,
        center=(x_center, y2),
        axes=(int(width), int(0.35 * width)),
        angle=0.0,
        startAngle=-45,
        endAngle=235,
        color=color,
        thickness=2,
        lineType=cv2.LINE_4,
    )
    if track_id is None:
        return frame
    rectangle_width = 40
    rectangle_height = 20
    x1_rect = x_center - rectangle_width // 2
    x2_rect = x_center + rectangle_width // 2
    y1_rect = (y2 - rectangle_height // 2) + 15
    y2_rect = (y2 + rectangle_height // 2) + 15
    cv2.rectangle(frame, (int(x1_rect), int(y1_rect)), (int(x2_rect), int(y2_rect)), color, cv2.FILLED)
    x1_text = x1_rect + 12
    if track_id > 99:
        x1_text -= 10
    cv2.putText(
        frame,
        f"{track_id}",
        (int(x1_text), int(y1_rect + 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 0),
        2,
    )
    return frame


def draw_ball_marker(frame, ball_info):
    """
    Draw distinctive ball marker (bright yellow circle + green triangle).
    
    Distinguishes between real detections and interpolated positions:
    - Real: Solid yellow circle
    - Interpolated: Dashed yellow circle
    
    Makes ball clearly visible against green pitch.
    """
    from utils import get_center_of_bbox
    
    bbox = ball_info.get("bbox")
    if not bbox:
        return frame
    
    center = get_center_of_bbox(bbox)
    center = tuple(map(int, center))
    
    is_interpolated = ball_info.get("interpolated", False)
    
    if is_interpolated:
        # Interpolated: dashed yellow circle (lighter, less certain)
        for angle in range(0, 360, 40):
            cv2.ellipse(frame, center, (8, 8), 0, angle, angle+20, 
                       (0, 255, 255), 2)
        cv2.circle(frame, center, 8, (0, 0, 0), 1)
    else:
        # Real detection: solid yellow circle + black outline
        cv2.circle(frame, center, 8, (0, 255, 255), -1)
        cv2.circle(frame, center, 8, (0, 0, 0), 2)
    
    # Green triangle above (for both types)
    y = int(bbox[1])
    x = center[0]
    triangle_points = np.array([[x, y], [x - 10, y - 20], [x + 10, y - 20]])
    cv2.drawContours(frame, [triangle_points], 0, (0, 255, 0), cv2.FILLED)
    cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)
    
    return frame


def draw_triangle(frame, bbox, color):
    """Draw indicator triangle (for possession or ball)."""
    from utils import get_center_of_bbox
    
    y = int(bbox[1])
    x, _ = get_center_of_bbox(bbox)
    triangle_points = np.array([[x, y], [x - 10, y - 20], [x + 10, y - 20]])
    cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
    cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)
    return frame


def draw_shot_status(frame, shot, frame_num, metrics_valid):
    """Shot status overlay removed — no longer drawn on video output."""
    return frame


def draw_team_ball_control_conditional(frame, frame_num, team_ball_control, show: bool):
    """
    Draw a clean ball control widget in the bottom-right corner.
    Shows team name, percentage and a colour progress bar.
    """
    h, w = frame.shape[:2]
    BOX_W, BOX_H = 360, 120
    x1 = w - BOX_W - 14
    y1 = h - BOX_H - 14

    # Semi-transparent dark background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x1 + BOX_W, y1 + BOX_H), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x1 + BOX_W, y1 + BOX_H), (180, 180, 180), 1)

    if not show:
        cv2.putText(frame, "Ball Control: N/A",
                    (x1 + 14, y1 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (160, 160, 160), 1)
        return frame

    until  = team_ball_control[: frame_num + 1]
    t1     = sum(1 for t in until if t == 1)
    t2     = sum(1 for t in until if t == 2)
    denom  = t1 + t2
    p1     = (t1 / denom) if denom else 0.5
    p2     = 1.0 - p1

    TEAM1_COLOR = (255, 255, 255)   # white
    TEAM2_COLOR = (0, 200, 80)      # green
    BAR_Y       = y1 + 85
    BAR_H       = 14
    BAR_X       = x1 + 14
    BAR_W       = BOX_W - 28

    # Labels
    cv2.putText(frame, f"Team 1  {p1*100:.1f}%",
                (x1 + 14, y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, TEAM1_COLOR, 2)
    cv2.putText(frame, f"Team 2  {p2*100:.1f}%",
                (x1 + 14, y1 + 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, TEAM2_COLOR, 2)

    # Split progress bar
    bar_t1 = int(BAR_W * p1)
    cv2.rectangle(frame, (BAR_X, BAR_Y), (BAR_X + bar_t1, BAR_Y + BAR_H),
                  TEAM1_COLOR, -1)
    cv2.rectangle(frame, (BAR_X + bar_t1, BAR_Y), (BAR_X + BAR_W, BAR_Y + BAR_H),
                  TEAM2_COLOR, -1)
    cv2.rectangle(frame, (BAR_X, BAR_Y), (BAR_X + BAR_W, BAR_Y + BAR_H),
                  (80, 80, 80), 1)

    return frame


def draw_minimap_conditional(frame, tracks, frame_num, pitch, show: bool):
    """
    Draw a proper pitch minimap with accurate markings.
    Includes: pitch outline, centre circle, centre line, penalty areas,
    goal areas, penalty spots, corner arcs.
    Only drawn when calibration is valid.
    """
    h, w = frame.shape[:2]

    # Minimap size and position — bottom-left, above ball control box
    MAP_W, MAP_H = 280, 182       # ~105:68 aspect ratio scaled up
    PAD           = 12
    x0 = PAD
    y0 = h - 170 - MAP_H - PAD   # sit just above the ball-control box

    if not show or pitch is None:
        return frame

    # ── Background ──────────────────────────────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + MAP_W, y0 + MAP_H), (34, 139, 34), -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    W, H = MAP_W, MAP_H   # shorthand
    L = pitch.length_m    # real-world metres
    Wd = pitch.width_m

    def m2px(mx, my):
        """Convert pitch metres to minimap pixel coords."""
        px = int(x0 + (mx / max(L, 1e-6)) * W)
        py = int(y0 + (my / max(Wd, 1e-6)) * H)
        return px, py

    def valid_pitch_position(position):
        return (
            isinstance(position, (list, tuple))
            and len(position) >= 2
            and np.isfinite(position[0])
            and np.isfinite(position[1])
            and 0 <= position[0] <= L
            and 0 <= position[1] <= Wd
        )

    WHITE = (255, 255, 255)
    lw = 1   # line width

    # ── Pitch outline ────────────────────────────────────────────────────
    cv2.rectangle(frame, m2px(0, 0), m2px(L, Wd), WHITE, lw)

    # ── Centre line ───────────────────────────────────────────────────────
    cv2.line(frame, m2px(L/2, 0), m2px(L/2, Wd), WHITE, lw)

    # ── Centre circle (r=9.15m) ───────────────────────────────────────────
    cx, cy = m2px(L/2, Wd/2)
    r_px   = int((9.15 / L) * W)
    cv2.circle(frame, (cx, cy), r_px, WHITE, lw)
    cv2.circle(frame, (cx, cy), 2, WHITE, -1)   # centre spot

    # ── Penalty areas (16.5m deep, 40.32m wide centred) ──────────────────
    pa_depth = 16.5
    pa_width = 40.32
    pa_side  = (Wd - pa_width) / 2

    # Left penalty area
    cv2.rectangle(frame,
                  m2px(0, pa_side),
                  m2px(pa_depth, Wd - pa_side),
                  WHITE, lw)
    # Right penalty area
    cv2.rectangle(frame,
                  m2px(L - pa_depth, pa_side),
                  m2px(L, Wd - pa_side),
                  WHITE, lw)

    # ── Goal areas (5.5m deep, 18.32m wide centred) ──────────────────────
    ga_depth = 5.5
    ga_width = 18.32
    ga_side  = (Wd - ga_width) / 2

    cv2.rectangle(frame,
                  m2px(0, ga_side),
                  m2px(ga_depth, Wd - ga_side),
                  WHITE, lw)
    cv2.rectangle(frame,
                  m2px(L - ga_depth, ga_side),
                  m2px(L, Wd - ga_side),
                  WHITE, lw)

    # ── Penalty spots ──────────────────────────────────────────────────────
    cv2.circle(frame, m2px(11.0, Wd/2), 2, WHITE, -1)
    cv2.circle(frame, m2px(L - 11.0, Wd/2), 2, WHITE, -1)

    # ── Corner arcs (r=1m, approximate) ──────────────────────────────────
    r_corner = max(1, int((1.0 / L) * W))
    for cx_m, cy_m, start_a, end_a in [
        (0,   0,    0,  90),
        (L,   0,   90, 180),
        (L,   Wd, 180, 270),
        (0,   Wd, 270, 360),
    ]:
        cv2.ellipse(frame, m2px(cx_m, cy_m), (r_corner, r_corner),
                    0, start_a, end_a, WHITE, lw)

    # ── Goals (simplified: thick short lines) ────────────────────────────
    goal_w = 7.32
    gs = (Wd - goal_w) / 2
    YELLOW = (0, 215, 255)
    cv2.line(frame, m2px(0, gs), m2px(0, Wd - gs), YELLOW, 2)
    cv2.line(frame, m2px(L, gs), m2px(L, Wd - gs), YELLOW, 2)

    # ── Players and ball ──────────────────────────────────────────────────
    def _objs(name):
        frames = tracks.get(name) or []
        return frames[frame_num] if frame_num < len(frames) else {}

    for _, player in _objs("players").items():
        pos = player.get("position_transformed")
        if not valid_pitch_position(pos):
            continue
        color = player.get("team_color", (0, 0, 255))
        px, py = m2px(pos[0], pos[1])
        cv2.circle(frame, (px, py), 4, color, -1)
        cv2.circle(frame, (px, py), 4, (0, 0, 0), 1)   # outline

    for _, gk in _objs("goalkeepers").items():
        pos = gk.get("position_transformed")
        if not valid_pitch_position(pos):
            continue
        px, py = m2px(pos[0], pos[1])
        cv2.circle(frame, (px, py), 5, gk.get("team_color", (0, 140, 255)), 2)

    for _, ball in _objs("ball").items():
        pos = ball.get("position_transformed")
        if not valid_pitch_position(pos):
            continue
        px, py = m2px(pos[0], pos[1])
        cv2.circle(frame, (px, py), 4, (0, 255, 255), -1)
        cv2.circle(frame, (px, py), 4, (0, 0, 0), 1)

    # ── Thin border ───────────────────────────────────────────────────────
    cv2.rectangle(frame, (x0, y0), (x0 + MAP_W, y0 + MAP_H), (200, 200, 200), 1)

    return frame


def draw_shot_aware_annotations(video_frames, tracks, team_ball_control, shots: List[Shot], pitch_mapper):
    """
    Draw annotations with shot-aware visibility control.
    
    Args:
        video_frames: List of video frames
        tracks: Player tracking data
        team_ball_control: Team possession array
        shots: List of Shot objects
        pitch_mapper: Shot-aware pitch mapper or regular pitch mapper
    """
    output = []
    
    # Build shot lookup
    shot_lookup = {}
    for idx, shot in enumerate(shots):
        for frame in range(shot.start_frame, shot.end_frame + 1):
            shot_lookup[frame] = idx
    
    for frame_num, frame in enumerate(video_frames):
        frame = frame.copy()

        def _objects(name):
            frames = tracks.get(name) or []
            if frame_num >= len(frames):
                return {}
            return frames[frame_num]

        # Get current shot
        shot_idx = shot_lookup.get(frame_num)
        shot = shots[shot_idx] if shot_idx is not None else None
        
        # Determine if metrics are valid for this frame
        metrics_valid = shot.metrics_enabled if shot else False
        
        # Get pitch mapper for this frame
        if hasattr(pitch_mapper, 'get_mapper_for_frame'):
            current_pitch = pitch_mapper.get_mapper_for_frame(frame_num)
        else:
            current_pitch = pitch_mapper if pitch_mapper and hasattr(pitch_mapper, 'H') else None

        # Draw players (always visible)
        for track_id, player in _objects("players").items():
            if player.get("ephemeral"):
                continue
            color = player.get("team_color", (0, 0, 255))
            frame = draw_ellipse(frame, player["bbox"], color, track_id)
            if player.get("has_ball"):
                frame = draw_triangle(frame, player["bbox"], (0, 0, 255))

        # Draw goalkeepers (always visible)
        for track_id, gk in _objects("goalkeepers").items():
            color = gk.get("team_color", (255, 0, 0))
            frame = draw_ellipse(frame, gk["bbox"], color, track_id)
            if gk.get("has_ball"):
                frame = draw_triangle(frame, gk["bbox"], (0, 0, 255))

        # Draw referees (always visible)
        for _, referee in _objects("referees").items():
            frame = draw_ellipse(frame, referee["bbox"], (0, 255, 255))

        # Draw ball (use distinctive marker)
        for _, ball in _objects("ball").items():
            if ball.get("bbox"):
                frame = draw_ball_marker(frame, ball)

        # Draw shot status indicator
        frame = draw_shot_status(frame, shot, frame_num, metrics_valid)
        
        # Draw minimap only if metrics valid
        frame = draw_minimap_conditional(frame, tracks, frame_num, current_pitch, show=metrics_valid)
        
        # Draw ball control only if metrics valid
        frame = draw_team_ball_control_conditional(frame, frame_num, team_ball_control, show=metrics_valid)
        
        output.append(frame)
    
    return output
