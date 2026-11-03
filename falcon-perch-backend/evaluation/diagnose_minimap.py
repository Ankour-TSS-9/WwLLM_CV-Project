"""
Phase G Part A — Minimap coordinate transformation diagnostic.

Inspects every transformation step and generates debug images for 6 sample
frames across the video. Produces a JSON report with per-frame diagnostics.

Run:
    python evaluation/diagnose_minimap.py
"""

import cv2
import json
import numpy as np
import os
import pickle
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils import get_foot_position, get_center_of_bbox, read_video

OUT_DIR = "evaluation/minimap_debug"
os.makedirs(OUT_DIR, exist_ok=True)


# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading stubs...")
with open("stubs/cv_full_tracks.pkl", "rb") as f:
    d = pickle.load(f)

tracks  = d["tracks"]
pitch   = d["pitch"]       # ShotAwarePitchMapper
camera  = d["camera"]      # {delta, cumulative, valid, shots}
fps     = d["fps"]

print(f"Frames: {len(tracks['players'])}  FPS: {fps}")

frames = read_video("input_videos/08fd33_4.mp4")
print(f"Video loaded: {len(frames)} frames")

# ── Identify sample frames (spread across video) ──────────────────────────────
n = len(frames)
sample_frames = sorted(set([
    0, n//6, n//3, n//2, 2*n//3, 5*n//6, n-1
]))
print(f"Sample frames: {sample_frames}")

# ── Get mapper details ────────────────────────────────────────────────────────
mapper_0 = pitch.get_mapper_for_frame(0)
if mapper_0:
    print(f"\nPitch mapper (frame 0):")
    print(f"  _auto_length_m = {mapper_0._auto_length_m:.2f}")
    print(f"  _auto_width_m  = {mapper_0._auto_width_m:.2f}")
    print(f"  length_m (FIFA)= {mapper_0.length_m:.2f}")
    print(f"  width_m  (FIFA)= {mapper_0.width_m:.2f}")
    print(f"  pixel_vertices:\n{mapper_0.pixel_vertices}")
    print(f"  H matrix:\n{np.round(mapper_0.H, 4) if mapper_0.H is not None else None}")

cum = camera.get("cumulative", [[0,0]]*n)
valid = camera.get("valid", [True]*n)

# ── Per-frame diagnostic ──────────────────────────────────────────────────────
report = {"frames": [], "summary": {}}

out_of_bounds_total = 0
in_bounds_total     = 0
no_transform_total  = 0

COLORS = {
    "team1": (255, 255, 255),
    "team2": (0, 200, 80),
    "ball":  (0, 255, 255),
    "out":   (0, 0, 255),
    "foot":  (0, 165, 255),
}

FIFA_L = 105.0
FIFA_W = 68.0
MAP_W  = 420
MAP_H  = int(MAP_W * FIFA_W / FIFA_L)   # ~272px — correct aspect ratio

for frame_idx in sample_frames:
    frame = frames[frame_idx].copy()
    h_f, w_f = frame.shape[:2]

    mapper = pitch.get_mapper_for_frame(frame_idx)
    cam_xy = cum[frame_idx] if frame_idx < len(cum) else [0.0, 0.0]
    cam_valid = valid[frame_idx] if frame_idx < len(valid) else True

    frame_report = {
        "frame": frame_idx,
        "camera_cumulative_px": cam_xy,
        "camera_valid": cam_valid,
        "mapper_found": mapper is not None,
        "players": [],
        "ball": None,
    }

    if mapper:
        frame_report["auto_length_m"]  = mapper._auto_length_m
        frame_report["auto_width_m"]   = mapper._auto_width_m
        frame_report["fifa_length_m"]  = mapper.length_m
        frame_report["fifa_width_m"]   = mapper.width_m
        frame_report["H_cond"]         = float(np.linalg.cond(mapper.H)) if mapper.H is not None else None

    # ── Draw pixel-space debug overlay ───────────────────────────────────────
    # 1. Grass quad (pitch boundary on screen)
    if mapper and mapper.pixel_vertices is not None:
        verts = mapper.pixel_vertices.astype(int)
        cv2.polylines(frame, [verts], True, (0, 255, 0), 2)
        for i, v in enumerate(verts):
            cv2.circle(frame, tuple(v), 6, (0, 255, 0), -1)
            cv2.putText(frame, f"V{i}", (v[0]+5, v[1]-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    # 2. Player footpoints
    player_frame = tracks["players"][frame_idx] if frame_idx < len(tracks["players"]) else {}
    for tid, info in player_frame.items():
        if info.get("ephemeral"):
            continue
        bbox = info.get("bbox")
        if not bbox:
            continue

        # Footpoint (what gets transformed)
        foot = get_foot_position(bbox)
        # position_adjusted (after camera compensation)
        pos_adj = info.get("position_adjusted")
        # position_transformed (final pitch coords)
        pos_t   = info.get("position_transformed")

        color = info.get("team_color", (128,128,128))
        cv2.circle(frame, foot, 4, COLORS["foot"], -1)
        cv2.circle(frame, foot, 4, (0,0,0), 1)
        cv2.putText(frame, str(tid), (foot[0]-8, foot[1]-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

        # Check if position_adjusted ≠ footpoint
        adj_applied = False
        if pos_adj:
            adj_diff = np.hypot(pos_adj[0] - foot[0], pos_adj[1] - foot[1])
            adj_applied = adj_diff > 0.5

        # Validate transform
        if pos_t is None:
            no_transform_total += 1
            pdata = {"id": tid, "foot_px": list(foot),
                     "adj_applied": adj_applied, "transform": None,
                     "status": "no_transform"}
        else:
            in_b = (0 <= pos_t[0] <= FIFA_L) and (0 <= pos_t[1] <= FIFA_W)
            if in_b:
                in_bounds_total += 1
                pdata = {"id": tid, "foot_px": list(foot),
                         "adj_applied": adj_applied,
                         "transform": pos_t, "status": "ok"}
            else:
                out_of_bounds_total += 1
                cv2.circle(frame, foot, 8, COLORS["out"], 2)
                pdata = {"id": tid, "foot_px": list(foot),
                         "adj_applied": adj_applied,
                         "transform": pos_t, "status": "out_of_bounds"}

        frame_report["players"].append(pdata)

    # 3. Ball
    ball_frame = tracks["ball"][frame_idx] if frame_idx < len(tracks["ball"]) else {}
    for _, binfo in ball_frame.items():
        bbox = binfo.get("bbox")
        if bbox:
            bc = get_center_of_bbox(bbox)
            cv2.circle(frame, bc, 6, COLORS["ball"], -1)
            pos_t = binfo.get("position_transformed")
            frame_report["ball"] = {"center_px": list(bc), "transform": pos_t}

    # Add camera info text
    cv2.putText(frame, f"F{frame_idx}  cam=({cam_xy[0]:.1f},{cam_xy[1]:.1f})  valid={cam_valid}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    # ── Draw minimap at correct aspect ratio ──────────────────────────────────
    minimap = np.zeros((MAP_H + 20, MAP_W + 20, 3), dtype=np.uint8)
    minimap[:] = (34, 139, 34)

    def m2map(mx, my):
        px = int(10 + (mx / FIFA_L) * MAP_W)
        py = int(10 + (my / FIFA_W) * MAP_H)
        return px, py

    WHITE = (255,255,255)
    lw = 1
    # Pitch outline
    cv2.rectangle(minimap, m2map(0,0), m2map(FIFA_L, FIFA_W), WHITE, lw)
    # Centre line
    cv2.line(minimap, m2map(FIFA_L/2,0), m2map(FIFA_L/2,FIFA_W), WHITE, lw)
    # Centre circle
    cx, cy = m2map(FIFA_L/2, FIFA_W/2)
    r_px = int((9.15/FIFA_L)*MAP_W)
    cv2.circle(minimap, (cx,cy), r_px, WHITE, lw)
    cv2.circle(minimap, (cx,cy), 2, WHITE, -1)
    # Penalty areas
    pa_d, pa_w = 16.5, 40.32
    pa_s = (FIFA_W - pa_w) / 2
    cv2.rectangle(minimap, m2map(0, pa_s), m2map(pa_d, FIFA_W-pa_s), WHITE, lw)
    cv2.rectangle(minimap, m2map(FIFA_L-pa_d, pa_s), m2map(FIFA_L, FIFA_W-pa_s), WHITE, lw)

    # Plot players
    for pdata in frame_report["players"]:
        pt = pdata.get("transform")
        if pt and 0 <= pt[0] <= FIFA_L and 0 <= pt[1] <= FIFA_W:
            tid = pdata["id"]
            # get team color from tracks
            pinfo = player_frame.get(tid, {})
            col = pinfo.get("team_color", (128,128,128))
            mp = m2map(pt[0], pt[1])
            cv2.circle(minimap, mp, 5, col, -1)
            cv2.circle(minimap, mp, 5, (0,0,0), 1)
            cv2.putText(minimap, str(tid), (mp[0]+4, mp[1]-4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
        elif pt:
            # Out of bounds — mark red
            mp_clamped = (int(np.clip(10+(pt[0]/FIFA_L)*MAP_W, 5, MAP_W+15)),
                           int(np.clip(10+(pt[1]/FIFA_W)*MAP_H, 5, MAP_H+15)))
            cv2.drawMarker(minimap, mp_clamped, (0,0,255), cv2.MARKER_CROSS, 10, 1)

    # Plot ball
    bpt = frame_report["ball"]["transform"] if frame_report.get("ball") else None
    if bpt and 0 <= bpt[0] <= FIFA_L and 0 <= bpt[1] <= FIFA_W:
        bmp = m2map(bpt[0], bpt[1])
        cv2.circle(minimap, bmp, 5, COLORS["ball"], -1)
        cv2.circle(minimap, bmp, 5, (0,0,0), 1)

    # ── Combine frame + minimap side by side ──────────────────────────────────
    # Resize frame to fixed height
    diag_h  = 540
    scale_f = diag_h / h_f
    frame_r = cv2.resize(frame, (int(w_f * scale_f), diag_h))
    map_r   = cv2.resize(minimap, (int((MAP_W+20)*diag_h/(MAP_H+20)), diag_h))
    combined = np.hstack([frame_r, map_r])

    out_path = os.path.join(OUT_DIR, f"frame_{frame_idx:04d}.jpg")
    cv2.imwrite(out_path, combined)
    print(f"  Saved: {out_path}")

    report["frames"].append(frame_report)

# ── Summary statistics ────────────────────────────────────────────────────────
# Full-video bounds check
print("\nRunning full-video bounds check...")
total_pts  = 0
oob_pts    = 0
no_trans   = 0
double_cam = 0   # check if camera correction is applied twice

for fidx, pframe in enumerate(tracks["players"]):
    cam = cum[fidx] if fidx < len(cum) else [0.0,0.0]
    for info in pframe.values():
        if info.get("ephemeral"):
            continue
        foot    = info.get("position")      # raw footpoint (no camera correction)
        adj     = info.get("position_adjusted")
        trans   = info.get("position_transformed")

        total_pts += 1

        if trans is None:
            no_trans += 1
            continue

        x, y = trans
        if not (0 <= x <= FIFA_L and 0 <= y <= FIFA_W):
            oob_pts += 1

        # Check double-application: if adj == foot, camera wasn't applied
        if adj and foot:
            diff = abs(adj[0] - foot[0]) + abs(adj[1] - foot[1])
            if diff < 0.1:
                pass   # camera correction was zero (static shot)

report["summary"] = {
    "total_player_points": total_pts,
    "out_of_bounds":       oob_pts,
    "no_transform":        no_trans,
    "oob_pct":             round(100 * oob_pts / max(total_pts,1), 2),
    "no_trans_pct":        round(100 * no_trans / max(total_pts,1), 2),
}

print(f"\n=== DIAGNOSTIC SUMMARY ===")
print(f"  Total player points : {total_pts}")
print(f"  Out of bounds       : {oob_pts}  ({report['summary']['oob_pct']:.1f}%)")
print(f"  No transform        : {no_trans}  ({report['summary']['no_trans_pct']:.1f}%)")

# Check transformation chain consistency
print(f"\n=== TRANSFORMATION CHAIN AUDIT ===")
f0_players = tracks["players"][0]
if f0_players:
    tid = next(iter(f0_players))
    info = f0_players[tid]
    print(f"  Sample player (ID {tid}) at frame 0:")
    print(f"    bbox             : {info.get('bbox')}")
    print(f"    position (foot)  : {info.get('position')}")
    print(f"    position_adjusted: {info.get('position_adjusted')}")
    print(f"    position_transf  : {info.get('position_transformed')}")
    cam0 = cum[0]
    foot = info.get("position")
    adj  = info.get("position_adjusted")
    if foot and adj:
        print(f"    camera[0] cumul  : {cam0}")
        print(f"    foot - adj       : ({foot[0]-adj[0]:.2f}, {foot[1]-adj[1]:.2f})")
        print(f"    (should match camera cumulative)")

    # Now manually re-transform footpoint → check against stored value
    mapper_0 = pitch.get_mapper_for_frame(0)
    if mapper_0:
        manual = mapper_0.transform_point(adj)
        stored = info.get("position_transformed")
        print(f"    manual transform : {manual}")
        print(f"    stored transform : {stored}")
        if manual and stored:
            diff = abs(manual[0]-stored[0]) + abs(manual[1]-stored[1])
            print(f"    diff             : {diff:.4f}m  {'OK' if diff < 0.1 else 'MISMATCH'}")

# Save report
report_path = os.path.join(OUT_DIR, "diagnostic_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\nFull report: {report_path}")
print(f"Debug images: {OUT_DIR}/frame_XXXX.jpg")
