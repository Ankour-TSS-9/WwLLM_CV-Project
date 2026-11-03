from collections import defaultdict

from cv import config
from cv.events import _to_native
from cv.tactics import occupancy_heatmaps, pass_network, team_shape, zone_name
from utils import measure_distance


def _control_share(team_ball_control):
    counts = {0: 0, 1: 0, 2: 0}
    for team in team_ball_control:
        counts[team if team in counts else 0] += 1
    known = counts[1] + counts[2]
    share = {1: 0.0, 2: 0.0}
    if known:
        share[1] = counts[1] / known
        share[2] = counts[2] / known
    return share, counts, known


def _path_stats(tracks, role_key, track_id, fps):
    frames = tracks.get(role_key, [])
    pts = []
    speeds = []
    on_ball = 0.0
    off_ball = 0.0
    prev = None
    prev_f = None
    prev_has = False
    for f, frame in enumerate(frames):
        info = frame.get(track_id)
        if not info:
            prev = None
            continue
        pos = info.get("position_transformed")
        speed = info.get("speed")
        # Only record valid speeds
        if speed is not None and 0 < speed <= config.MAX_PLAYER_KMH:
            speeds.append(float(speed))
        if pos is None:
            prev = None
            continue
        if prev is not None:
            step = measure_distance(prev, pos)
            dt = (f - prev_f) / fps if fps else 0
            # Validate step size to filter teleportation
            if 0 < step <= config.MAX_STEP_M * max(1, f - prev_f):
                if prev_has or info.get("has_ball"):
                    on_ball += step
                else:
                    off_ball += step
        prev = pos
        prev_f = f
        prev_has = bool(info.get("has_ball"))
    return {
        "distance_m": round(on_ball + off_ball, 2),
        "distance_on_ball_m": round(on_ball, 2),
        "distance_off_ball_m": round(off_ball, 2),
        "max_speed_kmh": round(max(speeds), 2) if speeds else 0.0,
        "avg_speed_kmh": round(sum(speeds) / len(speeds), 2) if speeds else 0.0,
    }


def _zone_counts(tracks, role_key, track_id, team, direction, pitch_length):
    counts = {"own_third": 0, "middle_third": 0, "final_third": 0, "unknown": 0}
    for frame in tracks.get(role_key, []):
        info = frame.get(track_id)
        if not info:
            continue
        pos = info.get("position_transformed")
        x = pos[0] if pos else None
        counts[zone_name(x, pitch_length, team, direction)] += 1
    return counts


def build_match_stats(
    tracks,
    holders,
    team_ball_control,
    events,
    fps,
    video_path,
    pitch=None,
    direction=None,
):
    n = len(tracks.get("players", []))
    duration = n / fps if fps else 0.0
    min_frames = max(8, int(round(config.MIN_STATS_S * fps)))
    pitch_length = pitch.length_m if pitch else config.PITCH_LENGTH
    pitch_width = pitch.width_m if pitch else config.PITCH_WIDTH
    direction = direction or {}
    possession_share, control_counts, known_poss = _control_share(team_ball_control)

    players = {}

    def ensure(role, track_id, team):
        key = f"{role}_{track_id}"
        if key not in players:
            players[key] = {
                "player_id": int(track_id),
                "role": role,
                "team": int(team) if team is not None else None,
                "frames_visible": 0,
                "minutes_visible": 0.0,
                "touches": 0,
                "passes": 0,
                "passes_received": 0,
                "progressive_passes": 0,
                "turnovers_lost": 0,
                "turnovers_won": 0,
                "carries": 0,
                "sprints": 0,
                "pressures_faced": 0,
                "box_entries": 0,
                "shots": 0,
            }
        return players[key]

    for role_key, role in (("players", "player"), ("goalkeepers", "goalkeeper")):
        visibility = defaultdict(int)
        team_of = {}
        for frame_tracks in tracks.get(role_key, []):
            for track_id, info in frame_tracks.items():
                if info.get("ephemeral"):
                    continue
                visibility[track_id] += 1
                if info.get("team") is not None:
                    team_of[track_id] = int(info["team"])
        for track_id, vis in visibility.items():
            if vis < min_frames:
                continue
            row = ensure(role, track_id, team_of.get(track_id))
            row["frames_visible"] = vis
            path = _path_stats(tracks, role_key, track_id, fps)
            row.update(path)
            row["minutes_visible"] = round(vis / fps / 60.0, 3) if fps else 0.0
            row["zone_frames"] = _zone_counts(
                tracks, role_key, track_id, row["team"], direction, pitch_length
            )

    last_holder = None
    for holder in holders:
        if holder is None:
            last_holder = None
            continue
        key, track_id, team = holder
        role = "goalkeeper" if key == "goalkeepers" else "player"
        row_key = f"{role}_{track_id}"
        if row_key not in players:
            continue
        if holder != last_holder:
            players[row_key]["touches"] += 1
        last_holder = holder

    def find_row(pid, team=None, role=None):
        for row in players.values():
            if row["player_id"] != pid:
                continue
            if team is not None and row["team"] != team:
                continue
            if role is not None and row["role"] != role:
                continue
            return row
        return None

    for event in events:
        et = event.get("type")
        if et == "pass":
            frm = find_row(event["from_player_id"], event.get("from_team"))
            to = find_row(event["to_player_id"], event.get("to_team"))
            if frm:
                frm["passes"] += 1
                if event.get("progressive"):
                    frm["progressive_passes"] += 1
            if to:
                to["passes_received"] += 1
        elif et == "turnover":
            lost = find_row(event["from_player_id"], event.get("from_team"))
            won = find_row(event["to_player_id"], event.get("to_team"))
            if lost:
                lost["turnovers_lost"] += 1
            if won:
                won["turnovers_won"] += 1
        elif et == "carry":
            row = find_row(event.get("player_id"), event.get("team"))
            if row:
                row["carries"] += 1
        elif et == "sprint":
            row = find_row(event.get("player_id"), event.get("team"), event.get("role"))
            if row:
                row["sprints"] += 1
        elif et == "pressure":
            row = find_row(event.get("player_id"), event.get("team"))
            if row:
                row["pressures_faced"] += 1
        elif et == "box_entry":
            row = find_row(event.get("player_id"), event.get("team"))
            if row:
                row["box_entries"] += 1
        elif et in ("shot", "shot_or_clearance"):
            row = find_row(event.get("player_id"), event.get("team"))
            if row:
                row["shots"] += 1

    event_counts = defaultdict(int)
    for event in events:
        event_counts[event["type"]] += 1

    heat_team, _ = occupancy_heatmaps(tracks, pitch_length, pitch_width)
    shapes = {1: [], 2: []}
    for f in range(0, n, max(1, int(fps))):
        for team in (1, 2):
            shape = team_shape(tracks, f, team)
            if shape:
                shapes[team].append(shape)

    def avg_shape(items):
        if not items:
            return None
        return {
            "centroid": [
                round(sum(s["centroid"][0] for s in items) / len(items), 2),
                round(sum(s["centroid"][1] for s in items) / len(items), 2),
            ],
            "width_m": round(sum(s["width_m"] for s in items) / len(items), 2),
            "length_m": round(sum(s["length_m"] for s in items) / len(items), 2),
        }

    team_stats = {}
    for team in (1, 2):
        team_players = [p for p in players.values() if p["team"] == team]
        team_stats[str(team)] = {
            "possession": round(possession_share.get(team, 0.0), 4),
            "possession_known_frames": known_poss,
            "players_tracked": len(team_players),
            "distance_m": round(sum(p.get("distance_m", 0) for p in team_players), 2),
            "passes": sum(p["passes"] for p in team_players),
            "progressive_passes": sum(p["progressive_passes"] for p in team_players),
            "turnovers_won": sum(p["turnovers_won"] for p in team_players),
            "sprints": sum(p["sprints"] for p in team_players),
            "box_entries": sum(p["box_entries"] for p in team_players),
            "shots": sum(p["shots"] for p in team_players),
            "attack_direction": direction.get(team),
            "shape": avg_shape(shapes[team]),
            "heatmap": heat_team[team],
        }

    stats = {
        "meta": {
            "video_path": video_path,
            "fps": round(float(fps), 3),
            "frames": n,
            "duration_s": round(duration, 2),
            "pitch_length_m": round(float(pitch_length), 2),
            "pitch_width_m": round(float(pitch_width), 2),
            "loose_ball_frames": control_counts[0],
            "possession_known_frames": known_poss,
            "min_player_visible_s": config.MIN_STATS_S,
            "note": (
                "Coordinates are meters on an auto-fitted pitch plane from frame 0. "
                "Ghost IDs shorter than min_player_visible_s are dropped from player sheets."
            ),
        },
        "teams": team_stats,
        "players": sorted(players.values(), key=lambda p: (p["team"] or 99, p["role"], -p["frames_visible"])),
        "pass_network": pass_network(events),
        "event_counts": dict(event_counts),
        "events": events,
    }
    return {k: _to_native(v) if not isinstance(v, (dict, list)) else v for k, v in stats.items()}
