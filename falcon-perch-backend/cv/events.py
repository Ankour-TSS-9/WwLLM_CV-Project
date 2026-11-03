from cv import config
from cv.tactics import in_penalty_box, zone_name
from utils import measure_distance


def _to_native(value):
    if hasattr(value, "item"):
        return value.item()
    return value


def _holder_segments(holders):
    segments = []
    i = 0
    n = len(holders)
    while i < n:
        if holders[i] is None:
            i += 1
            continue
        j = i + 1
        while j < n and holders[j] == holders[i]:
            j += 1
        key, player_id, team = holders[i]
        segments.append(
            {
                "start": i,
                "end": j - 1,
                "key": key,
                "player_id": player_id,
                "team": team,
            }
        )
        i = j
    return segments


def _ball_info(tracks, frame):
    ball = tracks.get("ball", [])
    if frame >= len(ball):
        return None
    return ball[frame].get(1)


def _ball_travel(tracks, start, end):
    a = _ball_info(tracks, start)
    b = _ball_info(tracks, end)
    if not a or not b:
        return 0.0, False, None, None, False
    detected_path = False
    for i in range(start, min(end + 1, len(tracks.get("ball", [])))):
        info = _ball_info(tracks, i)
        if info and info.get("detected"):
            detected_path = True
            break
    metric = False
    start_pos = a.get("position_transformed")
    end_pos = b.get("position_transformed")
    if start_pos is not None and end_pos is not None:
        metric = True
    else:
        start_pos = a.get("position")
        end_pos = b.get("position")
    if start_pos is None or end_pos is None:
        return 0.0, False, start_pos, end_pos, detected_path
    return measure_distance(start_pos, end_pos), metric, start_pos, end_pos, detected_path


def _max_ball_speed(tracks, start, end):
    best = 0.0
    for i in range(start, min(end + 1, len(tracks.get("ball", [])))):
        info = _ball_info(tracks, i)
        if not info:
            continue
        speed = info.get("speed")
        if speed is not None and speed <= config.MAX_BALL_KMH:
            best = max(best, speed)
    return best


def _player_xy(tracks, key, player_id, frame):
    frames = tracks.get(key) or []
    if frame >= len(frames) or player_id not in frames[frame]:
        return None
    return frames[frame][player_id].get("position_transformed")


def _classify_delivery(seg_a, travel, metric, speed, end_pos, direction, pitch):
    if not metric or end_pos is None or not direction or pitch is None:
        if speed >= config.SHOT_BALL_KMH:
            return "shot_or_clearance"
        return None
    team = seg_a["team"]
    if team not in direction:
        return None
    opp_x = direction[team]["opp_goal_x"]
    own_x = direction[team]["own_goal_x"]
    toward_opp = abs(end_pos[0] - opp_x) < abs(end_pos[0] - own_x)
    in_box = in_penalty_box(end_pos[0], end_pos[1], pitch.length_m, pitch.width_m, opp_x)
    is_gk = seg_a["key"] == "goalkeepers"
    if is_gk and speed >= config.CLEARANCE_BALL_KMH:
        return "gk_distribution"
    if toward_opp and in_box and speed >= config.SHOT_BALL_KMH:
        return "shot"
    if (not toward_opp) and speed >= config.CLEARANCE_BALL_KMH:
        return "clearance"
    if speed >= config.SHOT_BALL_KMH:
        return "shot_or_clearance"
    return None


def extract_events(tracks, holders, fps, direction=None, pitch=None):
    events = []
    segments = _holder_segments(holders)
    pitch_length = pitch.length_m if pitch else config.PITCH_LENGTH

    for seg in segments:
        start_xy = _player_xy(tracks, seg["key"], seg["player_id"], seg["start"])
        zone = zone_name(
            start_xy[0] if start_xy else None,
            pitch_length,
            seg["team"],
            direction or {},
        )
        events.append(
            {
                "time": round(seg["start"] / fps, 2),
                "frame": int(seg["start"]),
                "type": "possession_start",
                "team": seg["team"],
                "player_id": int(seg["player_id"]),
                "role": "goalkeeper" if seg["key"] == "goalkeepers" else "player",
                "duration_s": round((seg["end"] - seg["start"] + 1) / fps, 2),
                "zone": zone,
            }
        )

        travel, metric, _, _, _ = _ball_travel(tracks, seg["start"], seg["end"])
        min_carry = config.CARRY_MIN_PLAYER_TRAVEL_M if metric else config.CARRY_MIN_PLAYER_TRAVEL_PX
        if travel >= min_carry:
            events.append(
                {
                    "time": round(seg["start"] / fps, 2),
                    "frame": int(seg["start"]),
                    "type": "carry",
                    "team": seg["team"],
                    "player_id": int(seg["player_id"]),
                    "distance": round(travel, 2),
                    "unit": "m" if metric else "px",
                    "end_time": round(seg["end"] / fps, 2),
                    "zone": zone,
                }
            )

    seen_passes = set()
    for a, b in zip(segments, segments[1:]):
        travel, metric, start_pos, end_pos, detected_path = _ball_travel(
            tracks, a["end"], b["start"]
        )
        min_pass = config.PASS_MIN_BALL_TRAVEL_M if metric else config.PASS_MIN_BALL_TRAVEL_PX
        gap_s = (b["start"] - a["end"]) / fps
        
        # Require actual ball detection in the path
        if not detected_path or gap_s > config.PASS_MAX_GAP_S:
            continue

        payload = {
            "time": round(b["start"] / fps, 2),
            "frame": int(b["start"]),
            "from_player_id": int(a["player_id"]),
            "to_player_id": int(b["player_id"]),
            "from_team": a["team"],
            "to_team": b["team"],
            "ball_travel": round(travel, 2),
            "unit": "m" if metric else "px",
            "gap_s": round(gap_s, 2),
        }
        
        is_pass = (
            a["key"] == "players"
            and b["key"] == "players"
            and a["team"] in (1, 2)
            and a["team"] == b["team"]
            and a["player_id"] != b["player_id"]
            and b["start"] == a["end"] + 1
            and start_pos is not None
            and end_pos is not None
        )
        pass_key = (b["start"], a["team"], a["player_id"], b["player_id"])

        if is_pass and pass_key not in seen_passes:
            seen_passes.add(pass_key)
            payload["type"] = "pass"
            payload["team"] = a["team"]
            payload["team_id"] = int(a["team"])
            payload["passer_id"] = int(a["player_id"])
            payload["receiver_id"] = int(b["player_id"])
            from_xy = _player_xy(tracks, a["key"], a["player_id"], a["end"])
            payload["progressive"] = False
            if from_xy and end_pos and direction and a["team"] in direction:
                payload["progressive"] = abs(end_pos[0] - direction[a["team"]]["opp_goal_x"]) + 2 < abs(
                    from_xy[0] - direction[a["team"]]["opp_goal_x"]
                )
            events.append(payload)
        elif a["team"] != b["team"] and travel >= max(1.0, min_pass * 0.5):
            # Only record turnovers with reasonable travel
            payload["type"] = "turnover"
            payload["team"] = b["team"]
            events.append(payload)

        if travel < 1.0:
            continue

        ball_kmh = _max_ball_speed(tracks, a["end"], b["start"])
        kind = _classify_delivery(a, travel, metric, ball_kmh, end_pos, direction, pitch)
        if kind:
            events.append(
                {
                    "time": round(a["end"] / fps, 2),
                    "frame": int(a["end"]),
                    "type": kind,
                    "team": a["team"],
                    "player_id": int(a["player_id"]),
                    "ball_speed_kmh": round(ball_kmh, 1),
                    "role": "goalkeeper" if a["key"] == "goalkeepers" else "player",
                }
            )

    sprint_min_frames = max(4, int(round(config.SPRINT_MIN_S * fps)))
    cooldown = max(8, int(round(config.SPRINT_COOLDOWN_S * fps)))
    last_sprint = {}

    for key in ("players", "goalkeepers"):
        object_tracks = tracks.get(key, [])
        n = len(object_tracks)
        run_start = {}
        for frame_num in range(n):
            seen = set()
            for track_id, info in object_tracks[frame_num].items():
                if info.get("ephemeral"):
                    continue
                seen.add(track_id)
                speed = info.get("speed")
                if speed is None or speed < config.SPRINT_KMH or speed > config.MAX_PLAYER_KMH:
                    if track_id in run_start:
                        s0, max_speed, team = run_start.pop(track_id)
                        length = frame_num - s0
                        if (
                            length >= sprint_min_frames
                            and frame_num - last_sprint.get(track_id, -10_000) >= cooldown
                        ):
                            last_sprint[track_id] = s0
                            events.append(
                                {
                                    "time": round(s0 / fps, 2),
                                    "frame": int(s0),
                                    "type": "sprint",
                                    "team": team,
                                    "player_id": int(track_id),
                                    "role": "goalkeeper" if key == "goalkeepers" else "player",
                                    "speed_kmh": round(max_speed, 1),
                                    "duration_s": round(length / fps, 2),
                                }
                            )
                    continue
                if track_id not in run_start:
                    run_start[track_id] = [frame_num, speed, info.get("team")]
                else:
                    run_start[track_id][1] = max(run_start[track_id][1], speed)

            for track_id in list(run_start):
                if track_id in seen:
                    continue
                s0, max_speed, team = run_start.pop(track_id)
                length = frame_num - s0
                if length >= sprint_min_frames and frame_num - last_sprint.get(track_id, -10_000) >= cooldown:
                    last_sprint[track_id] = s0
                    events.append(
                        {
                            "time": round(s0 / fps, 2),
                            "frame": int(s0),
                            "type": "sprint",
                            "team": team,
                            "player_id": int(track_id),
                            "role": "goalkeeper" if key == "goalkeepers" else "player",
                            "speed_kmh": round(max_speed, 1),
                            "duration_s": round(length / fps, 2),
                        }
                    )

        for track_id, (s0, max_speed, team) in run_start.items():
            length = n - s0
            if length >= sprint_min_frames and n - last_sprint.get(track_id, -10_000) >= cooldown:
                events.append(
                    {
                        "time": round(s0 / fps, 2),
                        "frame": int(s0),
                        "type": "sprint",
                        "team": team,
                        "player_id": int(track_id),
                        "role": "goalkeeper" if key == "goalkeepers" else "player",
                        "speed_kmh": round(max_speed, 1),
                        "duration_s": round(length / fps, 2),
                    }
                )

    events.sort(key=lambda e: (e["time"], e["type"]))
    return [{k: _to_native(v) for k, v in e.items()} for e in events]
