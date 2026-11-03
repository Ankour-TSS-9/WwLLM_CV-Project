import cv2
import numpy as np
import sys

sys.path.append("../")
from utils import get_center_of_bbox, get_bbox_width


def draw_ellipse(frame, bbox, color, track_id=None):
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


def draw_triangle(frame, bbox, color):
    y = int(bbox[1])
    x, _ = get_center_of_bbox(bbox)
    triangle_points = np.array([[x, y], [x - 10, y - 20], [x + 10, y - 20]])
    cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
    cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)
    return frame


def draw_team_ball_control(frame, frame_num, team_ball_control):
    overlay = frame.copy()
    h, w = frame.shape[:2]
    x1, y1 = max(0, w - 570), max(0, h - 150)
    cv2.rectangle(overlay, (x1, y1), (w - 20, h - 20), (255, 255, 255), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    until = team_ball_control[: frame_num + 1]
    t1 = sum(1 for t in until if t == 1)
    t2 = sum(1 for t in until if t == 2)
    unknown = sum(1 for t in until if t == 0)
    denom = t1 + t2
    p1 = (t1 / denom) if denom else 0.0
    p2 = (t2 / denom) if denom else 0.0
    cv2.putText(
        frame,
        f"Team 1 Ball Control: {p1 * 100:.1f}%",
        (x1 + 20, y1 + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        frame,
        f"Team 2 Ball Control: {p2 * 100:.1f}%",
        (x1 + 20, y1 + 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        frame,
        f"Loose/unknown: {unknown} frames",
        (x1 + 20, y1 + 108),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        2,
    )
    return frame


def draw_minimap(frame, tracks, frame_num, pitch):
    if pitch is None or pitch.H is None:
        return frame
    map_w, map_h = 210, 136
    x0, y0 = 12, 110
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + map_w, y0 + map_h), (40, 120, 40), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.rectangle(frame, (x0, y0), (x0 + map_w, y0 + map_h), (255, 255, 255), 1)
    cv2.line(frame, (x0 + map_w // 2, y0), (x0 + map_w // 2, y0 + map_h), (255, 255, 255), 1)

    def to_map(pos):
        x = int(x0 + (pos[0] / max(pitch.length_m, 1e-6)) * map_w)
        y = int(y0 + (pos[1] / max(pitch.width_m, 1e-6)) * map_h)
        return x, y

    def objects(name):
        frames = tracks.get(name) or []
        if frame_num >= len(frames):
            return {}
        return frames[frame_num]

    for _, player in objects("players").items():
        pos = player.get("position_transformed")
        if not pos:
            continue
        color = player.get("team_color", (0, 0, 255))
        cv2.circle(frame, to_map(pos), 4, color, -1)
    for _, gk in objects("goalkeepers").items():
        pos = gk.get("position_transformed")
        if not pos:
            continue
        cv2.circle(frame, to_map(pos), 5, gk.get("team_color", (0, 140, 255)), 2)
    for _, ball in objects("ball").items():
        pos = ball.get("position_transformed")
        if not pos:
            continue
        cv2.circle(frame, to_map(pos), 3, (0, 255, 0), -1)
    return frame


def draw_annotations(video_frames, tracks, team_ball_control, pitch=None):
    output = []
    for frame_num, frame in enumerate(video_frames):
        frame = frame.copy()

        def _objects(name):
            frames = tracks.get(name) or []
            if frame_num >= len(frames):
                return {}
            return frames[frame_num]

        for track_id, player in _objects("players").items():
            if player.get("ephemeral"):
                continue
            color = player.get("team_color", (0, 0, 255))
            frame = draw_ellipse(frame, player["bbox"], color, track_id)
            if player.get("has_ball"):
                frame = draw_triangle(frame, player["bbox"], (0, 0, 255))

        for track_id, gk in _objects("goalkeepers").items():
            color = gk.get("team_color", (255, 0, 0))
            frame = draw_ellipse(frame, gk["bbox"], color, track_id)
            if gk.get("has_ball"):
                frame = draw_triangle(frame, gk["bbox"], (0, 0, 255))

        for _, referee in _objects("referees").items():
            frame = draw_ellipse(frame, referee["bbox"], (0, 255, 255))

        for _, ball in _objects("ball").items():
            if ball.get("bbox"):
                frame = draw_triangle(frame, ball["bbox"], (0, 255, 0))

        frame = draw_minimap(frame, tracks, frame_num, pitch)
        frame = draw_team_ball_control(frame, frame_num, team_ball_control)
        output.append(frame)
    return output
