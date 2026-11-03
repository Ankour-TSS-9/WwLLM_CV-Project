"""Match-level tactical features: attack direction, zones, shape, pressure, heatmaps."""

from collections import defaultdict

from utils import measure_distance

from cv import config


def _xy(info):
    pos = info.get("position_transformed")
    if pos is None or len(pos) < 2:
        return None
    return float(pos[0]), float(pos[1])


def infer_attack_direction(tracks, pitch_length):
    """Team defends the end where its keeper spends time. Attacks the opposite end."""
    gk_x = {1: [], 2: []}
    for frame in tracks.get("goalkeepers", []):
        for info in frame.values():
            xy = _xy(info)
            team = info.get("team")
            if xy is None or team not in gk_x:
                continue
            gk_x[team].append(xy[0])

    defend_x = {}
    for team in (1, 2):
        if gk_x[team]:
            defend_x[team] = float(sorted(gk_x[team])[len(gk_x[team]) // 2])
        else:
            xs = []
            for frame in tracks.get("players", []):
                for info in frame.values():
                    if info.get("team") != team:
                        continue
                    xy = _xy(info)
                    if xy is not None:
                        xs.append(xy[0])
            defend_x[team] = min(xs) if team == 1 and xs else (max(xs) if xs else 0.0)

    direction = {}
    for team in (1, 2):
        if defend_x[team] < pitch_length / 2:
            direction[team] = {
                "defends": "left",
                "attacks": "right",
                "attack_sign": 1,
                "own_goal_x": 0.0,
                "opp_goal_x": pitch_length,
            }
        else:
            direction[team] = {
                "defends": "right",
                "attacks": "left",
                "attack_sign": -1,
                "own_goal_x": pitch_length,
                "opp_goal_x": 0.0,
            }
    return direction


def zone_name(x, pitch_length, team, direction):
    if x is None or team not in direction:
        return "unknown"
    own = direction[team]["own_goal_x"]
    opp = direction[team]["opp_goal_x"]
    t = abs(x - own) / max(abs(opp - own), 1e-6)
    if t < 1 / 3:
        return "own_third"
    if t < 2 / 3:
        return "middle_third"
    return "final_third"


def in_penalty_box(x, y, pitch_length, pitch_width, goal_x):
    box_depth = 16.5
    box_half = 20.16
    mid_y = pitch_width / 2
    if abs(goal_x - 0.0) < 1e-6:
        in_x = 0 <= x <= box_depth
    else:
        in_x = pitch_length - box_depth <= x <= pitch_length
    in_y = mid_y - box_half <= y <= mid_y + box_half
    return bool(in_x and in_y)


def team_shape(tracks, frame_num, team):
    pts = []
    for key in ("players", "goalkeepers"):
        frame = tracks.get(key, [])
        if frame_num >= len(frame):
            continue
        for info in frame[frame_num].values():
            if info.get("team") != team or info.get("ephemeral"):
                continue
            xy = _xy(info)
            if xy is not None:
                pts.append(xy)
    if len(pts) < 4:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {
        "centroid": [round(sum(xs) / len(xs), 2), round(sum(ys) / len(ys), 2)],
        "width_m": round(max(ys) - min(ys), 2),
        "length_m": round(max(xs) - min(xs), 2),
        "n": len(pts),
    }


def occupancy_heatmaps(tracks, pitch_length, pitch_width, grid=(12, 8)):
    gx, gy = grid
    heat = {1: [[0] * gy for _ in range(gx)], 2: [[0] * gy for _ in range(gx)]}
    player_heat = defaultdict(lambda: [[0] * gy for _ in range(gx)])
    for key in ("players", "goalkeepers"):
        for frame in tracks.get(key, []):
            for pid, info in frame.items():
                if info.get("ephemeral"):
                    continue
                xy = _xy(info)
                team = info.get("team")
                if xy is None or team not in heat:
                    continue
                ix = int(min(gx - 1, max(0, xy[0] / pitch_length * gx)))
                iy = int(min(gy - 1, max(0, xy[1] / pitch_width * gy)))
                heat[team][ix][iy] += 1
                role = "goalkeeper" if key == "goalkeepers" else "player"
                player_heat[(role, pid, team)][ix][iy] += 1
    return heat, player_heat


def pressure_around_holder(tracks, holders, fps, pitch_ok):
    events = []
    last_emit = {}
    cooldown = max(8, int(round(0.8 * fps)))
    radius = config.PRESSURE_RADIUS_M if pitch_ok else config.PRESSURE_RADIUS_PX
    n = len(holders)
    for f, holder in enumerate(holders):
        if holder is None:
            continue
        h_key, h_id, h_team = holder
        frame_tracks = tracks.get(h_key) or []
        if f >= len(frame_tracks):
            continue
        h_info = frame_tracks[f].get(h_id)
        if not h_info:
            continue
        h_xy = _xy(h_info) if pitch_ok else (h_info.get("position") or (None, None))
        if h_xy is None or h_xy[0] is None:
            continue
        markers = []
        for key in ("players", "goalkeepers"):
            frame = tracks.get(key, [])
            if f >= len(frame):
                continue
            for pid, info in frame[f].items():
                if info.get("team") not in (1, 2) or info.get("team") == h_team:
                    continue
                if info.get("ephemeral"):
                    continue
                xy = _xy(info) if pitch_ok else info.get("position")
                if xy is None:
                    continue
                d = measure_distance(h_xy, xy)
                if d <= radius:
                    markers.append({"player_id": int(pid), "distance": round(d, 2)})
        if len(markers) >= 2:
            if f - last_emit.get(h_id, -10_000) < cooldown:
                continue
            last_emit[h_id] = f
            events.append(
                {
                    "time": round(f / fps, 2),
                    "frame": f,
                    "type": "pressure",
                    "team": h_team,
                    "player_id": int(h_id),
                    "pressing_team": 1 if h_team == 2 else 2,
                    "n_markers": len(markers),
                    "markers": markers[:6],
                }
            )
    return events


def pass_network(events):
    net = defaultdict(lambda: defaultdict(int))
    for e in events:
        if e.get("type") != "pass":
            continue
        net[int(e["from_player_id"])][int(e["to_player_id"])] += 1
    return {str(a): {str(b): n for b, n in bs.items()} for a, bs in net.items()}


def box_entries(tracks, holders, direction, pitch_length, pitch_width, fps):
    events = []
    last = {}
    for f, holder in enumerate(holders):
        if holder is None:
            continue
        key, pid, team = holder
        frame_tracks = tracks.get(key) or []
        if f >= len(frame_tracks):
            continue
        info = frame_tracks[f].get(pid)
        if not info:
            continue
        xy = _xy(info)
        if xy is None or team not in direction:
            continue
        opp = direction[team]["opp_goal_x"]
        if in_penalty_box(xy[0], xy[1], pitch_length, pitch_width, opp):
            if f - last.get((team, pid), -10_000) < int(fps):
                continue
            last[(team, pid)] = f
            events.append(
                {
                    "time": round(f / fps, 2),
                    "frame": f,
                    "type": "box_entry",
                    "team": team,
                    "player_id": int(pid),
                }
            )
    return events
