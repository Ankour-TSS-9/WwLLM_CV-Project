"""
Context-aware identity stitching with intelligent ephemeral filtering.

Key improvements:
1. Anti-collision constraint: prevents merging simultaneous players
2. Context-aware ephemeral filtering: preserves short tracks with evidence of validity
3. Temporal overlap detection: identifies truly distinct vs fragmented identities
"""

from collections import defaultdict
from cv import config
from utils import measure_distance


def _pos(info):
    return info.get("position_adjusted") or info.get("position")


def unify_role_for_shared_ids(tracks):
    """Consolidate IDs that flicker between player/goalkeeper roles."""
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
    """Split tracks into tracklets when gap > threshold."""
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
    """Create tracklet metadata from detection chunk."""
    first_pos = _pos(chunk[0][1])
    last_pos = _pos(chunk[-1][1])
    teams = [c[1].get("team") for c in chunk if c[1].get("team") in (1, 2)]
    team = max(set(teams), key=teams.count) if teams else None
    
    # Calculate average confidence
    confidences = [c[1].get("conf", 0.0) for c in chunk]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    
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
        "avg_conf": avg_conf,
    }


def _tracklets_overlap_in_time(tracklet_a, tracklet_b):
    """Check if two tracklets exist in any common frame."""
    start_a, end_a = tracklet_a["start"], tracklet_a["end"]
    start_b, end_b = tracklet_b["start"], tracklet_b["end"]
    return not (end_a < start_b or end_b < start_a)


def _get_overlapping_tracklets_in_component(comp_tracklets):
    """
    Find groups of tracklets that temporally overlap within a component.
    Returns list of sets, where each set contains indices of mutually overlapping tracklets.
    """
    n = len(comp_tracklets)
    overlap_graph = [set() for _ in range(n)]
    
    # Build overlap graph
    for i in range(n):
        for j in range(i + 1, n):
            if _tracklets_overlap_in_time(comp_tracklets[i], comp_tracklets[j]):
                overlap_graph[i].add(j)
                overlap_graph[j].add(i)
    
    # Find connected components in overlap graph
    visited = [False] * n
    overlap_groups = []
    
    for start in range(n):
        if visited[start]:
            continue
        # BFS to find all connected overlapping tracklets
        group = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if visited[node]:
                continue
            visited[node] = True
            group.add(node)
            for neighbor in overlap_graph[node]:
                if not visited[neighbor]:
                    queue.append(neighbor)
        overlap_groups.append(group)
    
    return overlap_groups


def _should_keep_short_track(component_tracklets, min_keep, debug=False):
    """
    Context-aware decision: should we keep this merged component despite being short?
    
    Evidence for keeping:
    - High detection count across component (approaching min_keep)
    - High average confidence (>= 0.5 for confidence-based retention)
    - Multiple distinct overlapping tracklets (evidence of real distinct players)
    - Temporal continuity (few gaps)
    
    Evidence for discarding:
    - Very few detections (< 12 frames = 0.48s)
    - Low average confidence (< 0.5 for short tracks)
    - Isolated single tracklet with no context
    """
    total_detections = sum(t["n"] for t in component_tracklets)
    
    # Already meets threshold - keep
    if total_detections >= min_keep:
        return True, "sufficient_detections"
    
    # Very short (< 12 frames = 0.48s) - likely false positive
    if total_detections < 12:
        return False, "too_few_detections"
    
    # Find overlapping tracklets (distinct simultaneous players)
    overlap_groups = _get_overlapping_tracklets_in_component(component_tracklets)
    has_overlaps = any(len(group) > 1 for group in overlap_groups)
    
    # If multiple tracklets coexist, they're distinct players - keep ALL
    if has_overlaps:
        return True, "distinct_simultaneous_players"
    
    # Single tracklet or sequential tracklets - apply stricter confidence threshold
    avg_conf = sum(t["avg_conf"] * t["n"] for t in component_tracklets) / total_detections
    
    # High confidence + moderate duration (>= 15 frames = 0.6s AND conf >= 0.5)
    if total_detections >= 15 and avg_conf >= 0.5:
        return True, "high_confidence_moderate_duration"
    
    # Approaching threshold with good confidence (>= 22 frames = 0.88s AND conf >= 0.4)
    if total_detections >= 22 and avg_conf >= 0.4:
        return True, "approaching_threshold_good_confidence"
    
    # Otherwise discard
    return False, "insufficient_evidence"


def stitch_identities_context_aware(tracks, fps, stitch_dist_px=None, stitch_gap_s=None, debug=False):
    """
    Context-aware identity stitching with intelligent ephemeral filtering.

    Args:
        tracks:        Track dictionary with players/goalkeepers
        fps:           Frames per second
        stitch_dist_px: Override default STITCH_DIST_PX (for F3 experiment)
        stitch_gap_s:  Override default STITCH_GAP_S (for F3 experiment)
        debug:         If True, log merge and filter decisions
    """
    unify_role_for_shared_ids(tracks)
    n = len(tracks.get("players", []))

    _gap_s    = stitch_gap_s   if stitch_gap_s   is not None else config.STITCH_GAP_S
    split_gap = max(8, int(round(_gap_s * fps)))
    stitch_gap = split_gap
    stitch_dist = stitch_dist_px if stitch_dist_px is not None else config.STITCH_DIST_PX

    tracklets = _split_tracklets(tracks, "players", split_gap)
    tracklets += _split_tracklets(tracks, "goalkeepers", split_gap)
    if not tracklets:
        return tracks

    # Multi-pass stitching with collision avoidance
    parent = list(range(len(tracklets)))
    merge_log = []
    collision_blocks = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def can_merge(i, j):
        """Check if merging i and j would violate collision constraint."""
        comp_i = [k for k in range(len(tracklets)) if find(k) == find(i)]
        comp_j = [k for k in range(len(tracklets)) if find(k) == find(j)]
        
        for ti in comp_i:
            for tj in comp_j:
                if _tracklets_overlap_in_time(tracklets[ti], tracklets[tj]):
                    return False
        return True

    def merge(i, j, reason=""):
        if not can_merge(i, j):
            if debug:
                a, b = tracklets[i], tracklets[j]
                collision_blocks.append({
                    "pass": reason,
                    "tracklet_a": f"{a['key'][:3]}_{a['orig']}",
                    "tracklet_b": f"{b['key'][:3]}_{b['orig']}",
                    "reason": "COLLISION - co-exist in frame",
                })
            return False
        
        parent[find(j)] = find(i)
        if debug:
            a, b = tracklets[i], tracklets[j]
            merge_log.append({
                "pass": reason,
                "tracklet_a": f"{a['key'][:3]}_{a['orig']}",
                "tracklet_b": f"{b['key'][:3]}_{b['orig']}",
                "gap_frames": b['start'] - a['end'],
            })
        return True

    # Pass 1: Strict merging
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
            
            if a["key"] == b["key"] and d < stitch_dist * 0.5:
                if a["team"] and b["team"] and a["team"] != b["team"]:
                    continue
                if merge(i, j, reason="pass1_strict"):
                    pass1_merges += 1

    # Pass 2: Role-flexible merging
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
            
            if a["team"] and b["team"] and a["team"] != b["team"]:
                continue
            
            d = measure_distance(a["last_pos"], b["first_pos"])
            score = d
            if a["key"] == b["key"]:
                score += config.STITCH_SAME_ROLE_BONUS
            else:
                score += config.STITCH_DIFF_ROLE_PENALTY
            
            if a["team"] and b["team"] and a["team"] == b["team"]:
                score += config.STITCH_SAME_TEAM_BONUS
            
            if score < stitch_dist * 0.8:
                if merge(i, j, reason="pass2_flexible"):
                    pass2_merges += 1

    # Pass 3: Gap-filling
    pass3_merges = 0
    orig_groups = defaultdict(list)
    for i, t in enumerate(tracklets):
        if t.get("orig"):
            orig_groups[t["orig"]].append(i)
    
    for orig_id, indices in orig_groups.items():
        if len(indices) <= 1:
            continue
        indices.sort(key=lambda i: tracklets[i]["start"])
        for idx in range(len(indices) - 1):
            i, j = indices[idx], indices[idx + 1]
            if find(i) == find(j):
                continue
            a, b = tracklets[i], tracklets[j]
            
            if a["team"] and b["team"] and a["team"] != b["team"]:
                continue
            
            if b["start"] - a["end"] <= stitch_gap * 1.5:
                if merge(i, j, reason="pass3_orig_id"):
                    pass3_merges += 1

    if debug:
        print(f"  Identity stitching: {len(tracklets)} tracklets -> {len(set(find(i) for i in range(len(tracklets))))} groups")
        print(f"  Stitch distance: {stitch_dist}px")
        print(f"  Pass1 (strict): {pass1_merges} merges")
        print(f"  Pass2 (flexible): {pass2_merges} merges")
        print(f"  Pass3 (orig_id): {pass3_merges} merges")
        print(f"  Collision blocks: {len(collision_blocks)}")

    # Group tracklets by component
    comps = defaultdict(list)
    for i in range(len(tracklets)):
        comps[find(i)].append(i)

    new_players = [{} for _ in range(n)]
    new_gks = [{} for _ in range(n)]
    next_id = 1
    min_keep = max(8, int(round(config.MIN_TRACK_S * fps)))

    # Context-aware ephemeral filtering
    kept_components = 0
    discarded_components = 0
    kept_reasons = defaultdict(int)
    discard_reasons = defaultdict(int)

    for members in sorted(comps.values(), key=lambda c: min(tracklets[i]["start"] for i in c)):
        component_tracklets = [tracklets[i] for i in members]
        
        # Apply context-aware filtering
        should_keep, reason = _should_keep_short_track(component_tracklets, min_keep, debug=debug)
        
        if should_keep:
            kept_components += 1
            kept_reasons[reason] += 1
        else:
            discarded_components += 1
            discard_reasons[reason] += 1
        
        # Determine role
        total_p = sum(t["n"] for t in component_tracklets if t["key"] == "players")
        total_g = sum(t["n"] for t in component_tracklets if t["key"] == "goalkeepers")
        role = "goalkeepers" if total_g > total_p else "players"
        dest = new_gks if role == "goalkeepers" else new_players
        
        cid = next_id
        next_id += 1
        
        for i in members:
            for f, info in tracklets[i]["items"]:
                if cid in dest[f]:
                    continue
                copied = dict(info)
                copied["ephemeral"] = not should_keep
                copied["orig_id"] = tracklets[i]["orig"]
                copied["filter_reason"] = reason
                dest[f][cid] = copied

    if debug:
        print(f"  Context-aware filtering:")
        print(f"    Kept: {kept_components} components")
        for reason, count in sorted(kept_reasons.items()):
            print(f"      {reason}: {count}")
        print(f"    Discarded: {discarded_components} components")
        for reason, count in sorted(discard_reasons.items()):
            print(f"      {reason}: {count}")

    tracks["players"] = new_players
    tracks["goalkeepers"] = new_gks
    return tracks
