import math
import sys

sys.path.append("../")
from utils import get_center_of_bbox, measure_distance

from cv import config


def _iter_on_field(tracks, frame_num):
    for key in ("players", "goalkeepers"):
        frame_tracks = tracks.get(key, [])
        if frame_num >= len(frame_tracks):
            continue
        for track_id, info in frame_tracks[frame_num].items():
            if info.get("ephemeral"):
                continue
            yield key, track_id, info


def _ball_point(tracks, frame_num):
    ball_frames = tracks.get("ball", [])
    if frame_num >= len(ball_frames):
        return None, None, None
    info = ball_frames[frame_num].get(1)
    if not info:
        return None, None, None
    transformed = info.get("position_transformed")
    if transformed is not None:
        return transformed, True, info
    pos = info.get("position")
    if pos is not None:
        return pos, False, info
    bbox = info.get("bbox")
    if bbox:
        return get_center_of_bbox(bbox), False, info
    return None, None, None


def _player_point(info):
    transformed = info.get("position_transformed")
    if transformed is not None:
        return transformed, True
    pos = info.get("position")
    if pos is not None:
        return pos, False
    bbox = info.get("bbox")
    if bbox:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, y2), False
    return None, False


def nearest_player_to_ball(tracks, frame_num):
    ball_pt, ball_metric, ball_info = _ball_point(tracks, frame_num)
    if ball_pt is None:
        return None

    best = None
    best_dist = math.inf

    for key, track_id, info in _iter_on_field(tracks, frame_num):
        player_pt, player_metric = _player_point(info)
        if player_pt is None:
            continue
        metric = bool(ball_metric and player_metric)
        dist = measure_distance(player_pt, ball_pt)
        limit = config.POSSESSION_MAX_DIST_M if metric else config.POSSESSION_MAX_DIST_PX
        if dist > limit:
            continue
        if dist < best_dist:
            best_dist = dist
            close = dist <= (config.POSSESSION_CLOSE_DIST_M if metric else config.POSSESSION_CLOSE_DIST_PX)
            best = {
                "key": key,
                "player_id": track_id,
                "team": info.get("team"),
                "distance": dist,
                "meters": metric,
                "close": close,
                "interpolated": bool(ball_info.get("interpolated")) if ball_info else False,
            }
    return best


def assign_possession(tracks, fps):
    n = len(tracks.get("players", []))
    min_hold = max(2, int(round(config.POSSESSION_MIN_HOLD_S * fps)))
    lost_hold = max(3, int(round(config.POSSESSION_LOST_S * fps)))

    holders = [None] * n
    current = None
    pending = None
    pending_count = 0
    none_count = 0

    for frame_num in range(n):
        nearest = nearest_player_to_ball(tracks, frame_num)
        cand = None
        need = min_hold
        if nearest is not None:
            cand = (nearest["key"], nearest["player_id"], nearest["team"])
            if nearest.get("close"):
                need = max(2, min_hold - 2)

        if cand is None:
            none_count += 1
            pending = None
            pending_count = 0
            if current is not None and none_count >= lost_hold:
                current = None
        else:
            none_count = 0
            if current is not None and cand[0] == current[0] and cand[1] == current[1]:
                pending = None
                pending_count = 0
            else:
                if pending == cand:
                    pending_count += 1
                else:
                    pending = cand
                    pending_count = 1
                if pending_count >= need:
                    current = cand
                    pending = None
                    pending_count = 0

        holders[frame_num] = current
        if current is not None:
            key, track_id, _team = current
            frame_tracks = tracks.get(key, [])
            if frame_num < len(frame_tracks) and track_id in frame_tracks[frame_num]:
                frame_tracks[frame_num][track_id]["has_ball"] = True

    # Unknown frames stay 0 — do not copy last team into empty possession.
    team_ball_control = []
    for holder in holders:
        if holder is not None and holder[2] in (1, 2):
            team_ball_control.append(holder[2])
        else:
            team_ball_control.append(0)

    return holders, team_ball_control
