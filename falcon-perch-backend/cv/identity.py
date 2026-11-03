"""Merge flickering GK/player IDs and stitch short tracklets of the same person."""

from collections import defaultdict

from utils import measure_distance

from cv import config


def _pos(info):
    return info.get("position_adjusted") or info.get("position")


def unify_role_for_shared_ids(tracks):
    n = len(tracks.get("players", []))
    p_ids, g_ids = set(), set()
    p_count, g_count = defaultdict(int), defaultdict(int)
    for f in range(n):
        for tid in tracks["players"][f]:
            p_ids.add(tid)
            p_count[tid] += 1
        for tid in tracks["goalkeepers"][f]:
            g_ids.add(tid)
            g_count[tid] += 1

    for tid in p_ids & g_ids:
        majority = "goalkeepers" if g_count[tid] > p_count[tid] else "players"
        other = "players" if majority == "goalkeepers" else "goalkeepers"
        for f in range(n):
            if tid in tracks[other][f]:
                if tid not in tracks[majority][f]:
                    tracks[majority][f][tid] = tracks[other][f].pop(tid)
                else:
                    tracks[other][f].pop(tid)


def _split_tracklets(tracks, key, gap):
    appearances = defaultdict(list)
    for f, frame in enumerate(tracks.get(key, [])):
        for tid, info in frame.items():
            appearances[tid].append((f, info))

    tracklets = []
    for tid, apps in appearances.items():
        apps.sort()
        chunk = [apps[0]]
        for item in apps[1:]:
            if item[0] - chunk[-1][0] > gap:
                tracklets.append(_make_tracklet(key, tid, chunk))
                chunk = [item]
            else:
                chunk.append(item)
        tracklets.append(_make_tracklet(key, tid, chunk))
    return tracklets


def _make_tracklet(key, tid, chunk):
    first_pos = _pos(chunk[0][1])
    last_pos = _pos(chunk[-1][1])
    teams = [c[1].get("team") for c in chunk if c[1].get("team") in (1, 2)]
    team = max(set(teams), key=teams.count) if teams else None
    return {
        "key": key,
        "orig": tid,
        "start": chunk[0][0],
        "end": chunk[-1][0],
        "n": len(chunk),
        "first_pos": first_pos,
        "last_pos": last_pos,
        "team": team,
        "items": chunk,
    }


def stitch_identities(tracks, fps, debug=False):
    """Enhanced identity stitching with multi-pass merging.
    
    Args:
        tracks: Track dictionary with players/goalkeepers
        fps: Frames per second
        debug: If True, log merge decisions
    """
    unify_role_for_shared_ids(tracks)
    n = len(tracks.get("players", []))
    split_gap = max(8, int(round(config.STITCH_GAP_S * fps)))
    stitch_gap = split_gap
    stitch_dist = config.STITCH_DIST_PX

    tracklets = _split_tracklets(tracks, "players", split_gap)
    tracklets += _split_tracklets(tracks, "goalkeepers", split_gap)
    if not tracklets:
        return tracks

    # Multi-pass stitching: first strict, then relaxed
    parent = list(range(len(tracklets)))
    merge_log = []  # Track merge decisions for diagnostics

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def merge(i, j, reason=""):
        parent[find(j)] = find(i)
        if debug:
            a, b = tracklets[i], tracklets[j]
            merge_log.append({
                "pass": reason,
                "tracklet_a": f"{a['key'][:3]}_{a['orig']}",
                "tracklet_b": f"{b['key'][:3]}_{b['orig']}",
                "frames_a": f"{a['start']}-{a['end']}",
                "frames_b": f"{b['start']}-{b['end']}",
                "gap_frames": b['start'] - a['end'],
                "team_a": a['team'],
                "team_b": b['team'],
            })

    # Pass 1: Strict merging (same role, close distance, same team)
    pass1_merges = 0
    for i in range(len(tracklets)):
        a = tracklets[i]
        if a["last_pos"] is None:
            continue
        for j in range(i + 1, len(tracklets)):
            b = tracklets[j]
            if find(i) == find(j):
                continue
            if b["start"] <= a["end"] or b["start"] - a["end"] > stitch_gap:
                continue
            if b["first_pos"] is None:
                continue
            
            d = measure_distance(a["last_pos"], b["first_pos"])
            if d > stitch_dist:
                continue
            
            # Strict: same role, close distance, same team (or both unknown)
            if a["key"] == b["key"] and d < stitch_dist * 0.5:
                # Only merge if same team OR at least one team is unknown
                if a["team"] and b["team"] and a["team"] != b["team"]:
                    continue  # Different teams - skip
                merge(i, j, reason="pass1_strict")
                pass1_merges += 1

    # Pass 2: Role-flexible merging (allow player <-> goalkeeper with position continuity)
    pass2_merges = 0
    for i in range(len(tracklets)):
        a = tracklets[i]
        if a["last_pos"] is None:
            continue
        for j in range(i + 1, len(tracklets)):
            b = tracklets[j]
            if find(i) == find(j):
                continue
            if b["start"] <= a["end"] or b["start"] - a["end"] > stitch_gap:
                continue
            if b["first_pos"] is None:
                continue
            
            # Block cross-team merges entirely (don't just penalize)
            if a["team"] and b["team"] and a["team"] != b["team"]:
                continue
            
            d = measure_distance(a["last_pos"], b["first_pos"])
            
            # Calculate score with bonuses/penalties
            score = d
            if a["key"] == b["key"]:
                score += config.STITCH_SAME_ROLE_BONUS
            else:
                score += config.STITCH_DIFF_ROLE_PENALTY
            
            if a["team"] and b["team"] and a["team"] == b["team"]:
                score += config.STITCH_SAME_TEAM_BONUS
            
            # Merge if score is reasonable
            if score < stitch_dist * 0.8:
                merge(i, j, reason="pass2_flexible")
                pass2_merges += 1

    # Pass 3: Gap-filling (same original ID appearing again)
    pass3_merges = 0
    orig_groups = defaultdict(list)
    for i, t in enumerate(tracklets):
        if t.get("orig"):
            orig_groups[t["orig"]].append(i)
    
    for orig_id, indices in orig_groups.items():
        if len(indices) <= 1:
            continue
        # Sort by start time
        indices.sort(key=lambda i: tracklets[i]["start"])
        # Merge consecutive fragments (but check team consistency)
        for idx in range(len(indices) - 1):
            i, j = indices[idx], indices[idx + 1]
            if find(i) == find(j):
                continue
            a, b = tracklets[i], tracklets[j]
            
            # Check team consistency: only merge if same team or team unknown
            if a["team"] and b["team"] and a["team"] != b["team"]:
                continue  # Don't merge different teams even with same orig ID
            
            if b["start"] - a["end"] <= stitch_gap * 1.5:
                merge(i, j, reason="pass3_orig_id")
                pass3_merges += 1

    if debug:
        print(f"  Identity stitching: {len(tracklets)} tracklets → {len(set(find(i) for i in range(len(tracklets))))} groups")
        print(f"  Pass1 (strict): {pass1_merges} merges")
        print(f"  Pass2 (flexible): {pass2_merges} merges")
        print(f"  Pass3 (orig_id): {pass3_merges} merges")
        if merge_log:
            print(f"  Sample merges:")
            for log in merge_log[:5]:
                team_info = f"team {log['team_a']}→{log['team_b']}" if log['team_a'] and log['team_b'] else "no team"
                print(f"    {log['pass']}: {log['tracklet_a']} + {log['tracklet_b']} (gap={log['gap_frames']}f, {team_info})")

    comps = defaultdict(list)
    for i in range(len(tracklets)):
        comps[find(i)].append(i)

    new_players = [{} for _ in range(n)]
    new_gks = [{} for _ in range(n)]
    next_id = 1
    min_keep = max(8, int(round(config.MIN_TRACK_S * fps)))

    for members in sorted(comps.values(), key=lambda c: min(tracklets[i]["start"] for i in c)):
        total_p = sum(tracklets[i]["n"] for i in members if tracklets[i]["key"] == "players")
        total_g = sum(tracklets[i]["n"] for i in members if tracklets[i]["key"] == "goalkeepers")
        total = total_p + total_g
        ephemeral = total < min_keep
        role = "goalkeepers" if total_g > total_p else "players"
        dest = new_gks if role == "goalkeepers" else new_players
        cid = next_id
        next_id += 1
        for i in members:
            for f, info in tracklets[i]["items"]:
                if cid in dest[f]:
                    continue
                copied = dict(info)
                copied["ephemeral"] = ephemeral
                copied["orig_id"] = tracklets[i]["orig"]
                dest[f][cid] = copied

    tracks["players"] = new_players
    tracks["goalkeepers"] = new_gks
    return tracks
