"""
Shot-aware CV pipeline with broadcast shot detection.

Usage:
    python run_cv_shot_aware.py --video input_videos/arsenal-vs-everton.mp4
    python run_cv_shot_aware.py --video input_videos/arsenal-vs-everton.mp4 --no-stub
    python run_cv_shot_aware.py --video input_videos/arsenal-vs-everton.mp4 --no-shot-detection

Writes:
    stats/match_stats.json
    stats/events.json
    stats/shots.json  (when shot detection enabled)
    output_videos/cv_output.avi
"""

import argparse
import json
import os
import pickle

import numpy as np

from utils import read_video, save_video, get_video_fps, estimate_ram_gb, get_video_frame_count
from cv.tracker import ImprovedTracker
from cv.camera import ImprovedCameraEstimator
from cv.orb_camera import ORBCameraEstimator
from cv.shot_detector import ShotDetector
from cv.shot_aware_camera import ShotAwareCameraEstimator
from cv.shot_aware_pitch import ShotAwarePitchMapper
from cv.shot_aware_speed import draw_speed_and_distance_conditional
from cv.speed import ImprovedSpeedEstimator
from cv.team_assigner import ImprovedTeamAssigner
from cv.possession import assign_possession
from cv.events import extract_events
from cv.stats import build_match_stats
from cv.annotate import draw_annotations
from cv.shot_aware_annotate import draw_shot_aware_annotations

# Phase C: Use context-aware identity filtering (evaluated improvement: +2.8pp retention)
USE_CONTEXT_AWARE_FILTERING = True

if USE_CONTEXT_AWARE_FILTERING:
    from cv.identity_context_aware import stitch_identities_context_aware as stitch_identities
else:
    from cv.identity import stitch_identities

from cv.pitch import PitchMapper, add_transformed_positions
from cv.tactics import box_entries, infer_attack_direction, pressure_around_holder
from cv import config


def _json_default(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")


def run(video_path, model_path, read_from_stub, skip_video, shot_aware=True):
    if not os.path.exists(video_path):
        raise FileNotFoundError(
            f"Video not found: {video_path}. Put a clip in input_videos/ or pass --video."
        )
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"YOLO weights not found: {model_path}. The base detector is models/best.pt."
        )

    os.makedirs("stubs", exist_ok=True)
    os.makedirs("stats", exist_ok=True)
    os.makedirs("output_videos", exist_ok=True)

    fps = get_video_fps(video_path)
    # Validate FPS (must be reasonable for video analysis)
    if fps < 15 or fps > 60 or not np.isfinite(fps):
        print(f"Warning: Unusual FPS {fps:.2f}, defaulting to 25.0")
        fps = 25.0
    print(f"Reading {video_path} ({fps:.2f} fps)...")

    # ── Auto-clip: if video exceeds RAM limit, cut it to a safe length ──────
    ram_needed_gb = estimate_ram_gb(video_path)
    total_frames  = get_video_frame_count(video_path)
    duration_min  = total_frames / fps / 60
    RAM_LIMIT_GB  = 16.0   # ~2/3 of 24 GB physical RAM

    if ram_needed_gb > RAM_LIMIT_GB:
        # Calculate how many seconds fit inside the RAM limit
        max_frames   = int((RAM_LIMIT_GB / ram_needed_gb) * total_frames * 0.9)
        max_seconds  = max_frames / fps
        max_minutes  = max_seconds / 60

        import subprocess, pathlib
        base      = pathlib.Path(video_path).stem
        clip_path = str(pathlib.Path(video_path).parent / f"{base}_autoclip.mp4")

        print(f"\n  Video is {duration_min:.1f} min and needs {ram_needed_gb:.1f} GB RAM "
              f"(limit: {RAM_LIMIT_GB:.1f} GB).")
        print(f"  Auto-clipping to first {max_minutes:.1f} minutes -> {clip_path}")

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path,
             "-ss", "00:00:00",
             "-t",  str(int(max_seconds)),
             "-c",  "copy",
             clip_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg auto-clip failed.\n{result.stderr}\n\n"
                f"Install ffmpeg or manually trim the video to under "
                f"{max_minutes:.0f} minutes and re-run."
            )

        print(f"  Clip written: {clip_path}")
        video_path    = clip_path           # continue with the clipped file
        ram_needed_gb = estimate_ram_gb(video_path)
        total_frames  = get_video_frame_count(video_path)
        duration_min  = total_frames / fps / 60
        print(f"  New video: {total_frames} frames, "
              f"{duration_min:.1f} min, ~{ram_needed_gb:.1f} GB RAM\n")
    elif ram_needed_gb > RAM_LIMIT_GB * 0.7:
        print(f"  Warning: video will use ~{ram_needed_gb:.1f} GB RAM. "
              f"Close other apps if processing fails.")
    elif ram_needed_gb > RAM_LIMIT_GB * 0.6:
        print(f"  Warning: video will use ~{ram_needed_gb:.1f} GB RAM "
              f"({total_frames:,} frames, {duration_min:.1f} min). "
              f"Close other apps if processing fails.")

    video_frames = read_video(video_path)
    
    # Shot detection
    shots = []
    if shot_aware:
        print("\n=== SHOT DETECTION ===")
        detector = ShotDetector(fps=fps)
        shots = detector.detect_shots(video_frames)
        
        # Save shot summary
        shot_summary = detector.shots_to_dict(shots)
        with open("stats/shots.json", "w", encoding="utf-8") as f:
            json.dump({"shots": shot_summary, "total_shots": len(shots)}, f, indent=2)
        print(f"Wrote stats/shots.json")

    tracker = ImprovedTracker(model_path)
    print("\n=== OBJECT DETECTION & TRACKING ===")
    # F2: Apply configured inference resolution
    _imgsz = config.INFERENCE_IMGSZ
    if _imgsz != 640:
        print(f"  Inference resolution: {_imgsz} (F2 flag)")
    # Temporarily patch config so ImprovedTracker.detect_frames uses it
    tracker._imgsz_override = _imgsz
    tracks = tracker.get_object_tracks(
        video_frames,
        read_from_stub=read_from_stub,
        stub_path="stubs/cv_tracks.pkl",
    )
    n_frames = len(video_frames)

    # Guard: discard a cached stub that was built from a different-length video.
    # If any track list is longer than the current video, the stub is stale and
    # must be re-generated so all downstream index arithmetic stays consistent.
    stub_frame_count = max(
        (len(tracks.get(k, [])) for k in ("players", "goalkeepers", "referees", "ball")),
        default=0,
    )
    if stub_frame_count > n_frames:
        import warnings
        warnings.warn(
            f"Cached tracks stub has {stub_frame_count} frames but video has "
            f"{n_frames} frames. Discarding stale stub and re-running detection.",
            stacklevel=2,
        )
        tracks = tracker.get_object_tracks(
            video_frames,
            read_from_stub=False,
            stub_path="stubs/cv_tracks.pkl",
        )

    for key in ("players", "goalkeepers", "referees", "ball"):
        tracks.setdefault(key, [])
        while len(tracks[key]) < n_frames:
            tracks[key].append({})

    print("Interpolating short ball gaps...")
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])
    
    tracker.add_position_to_tracks(tracks)

    # Camera motion estimation - shot-aware
    print("\n=== CAMERA MOTION ESTIMATION ===")
    # F1: Choose camera estimator based on flag
    _use_orb = config.USE_ORB_GMC
    if _use_orb:
        print("  Camera method: ORB GMC (F1 flag, approved Phase E1.5)")
        _base_cam = ORBCameraEstimator(video_frames[0])
    else:
        print("  Camera method: Lucas-Kanade (baseline)")
        _base_cam = ImprovedCameraEstimator(video_frames[0])

    if shot_aware and shots:
        print("  Using shot-aware estimation...")
        camera_estimator = ShotAwareCameraEstimator(_base_cam, shots)
        camera = camera_estimator.get_camera_movement(video_frames, tracks=tracks)
        camera_estimator.add_adjust_positions_to_tracks(tracks, camera)
    else:
        print("  Using standard estimation...")
        camera = _base_cam.get_camera_movement(
            video_frames,
            tracks=tracks,
            read_from_stub=read_from_stub,
            stub_path="stubs/cv_camera.pkl",
        )
        _base_cam.add_adjust_positions_to_tracks(tracks, camera["cumulative"])
        camera["valid"] = [True] * n_frames
    camera_estimator = camera_estimator if (shot_aware and shots) else _base_cam

    print("\n=== TEAM ASSIGNMENT & IDENTITY STITCHING ===")
    print("Assigning teams (pre-stitching)...")
    team_assigner = ImprovedTeamAssigner()
    team_assigner.assign_team_color(video_frames, tracks["players"])
    team_assigner.assign_all_players(video_frames, tracks)

    print("Stitching player identities (with team info)...")
    # F3: Optionally use widened stitching thresholds
    if config.USE_F3_STITCH:
        print(f"  Stitching thresholds: dist={config.STITCH_DIST_PX_F3}px, gap={config.STITCH_GAP_S_F3}s (F3 flag)")
        stitch_identities(tracks, fps, stitch_dist_px=config.STITCH_DIST_PX_F3,
                          stitch_gap_s=config.STITCH_GAP_S_F3, debug=True)
    else:
        stitch_identities(tracks, fps, debug=True)

    # Pitch calibration - shot-aware
    print("\n=== PITCH CALIBRATION ===")
    if shot_aware and shots:
        print("Using shot-aware pitch calibration...")
        pitch_mapper = ShotAwarePitchMapper(shots)
        pitch_mapper.fit_shots(video_frames, tracks)
        pitch_mapper.add_transformed_positions(tracks, camera)
        
        # Get representative dimensions (from first valid shot)
        pitch_length, pitch_width = config.PITCH_LENGTH, config.PITCH_WIDTH
        for shot in shots:
            mapper = pitch_mapper.get_mapper_for_frame(shot.start_frame)
            if mapper:
                pitch_length, pitch_width = mapper.length_m, mapper.width_m
                break
        print(f"Representative pitch dimensions: {pitch_length:.1f}m × {pitch_width:.1f}m")
        pitch = pitch_mapper  # Use shot-aware mapper
    else:
        print("Using standard pitch calibration...")
        pitch = PitchMapper(video_frames[0], tracks["players"][0] if tracks["players"] else {})
        add_transformed_positions(tracks, pitch)
        pitch_length, pitch_width = pitch.length_m, pitch.width_m
        print(f"Pitch plane: {pitch_length:.1f}m × {pitch_width:.1f}m")

    print("\n=== METRICS COMPUTATION ===")
    print("Speed / distance...")
    speed_estimator = ImprovedSpeedEstimator(fps)
    speed_estimator.add_speed_and_distance_to_tracks(tracks)

    print("Possession...")
    holders, team_ball_control = assign_possession(tracks, fps)

    print("Tactics and events...")
    # Use representative pitch dimensions
    direction = infer_attack_direction(tracks, pitch_length)
    
    # Pass pitch mapper for event extraction
    events = extract_events(tracks, holders, fps, direction=direction, pitch=pitch)
    events += pressure_around_holder(tracks, holders, fps, pitch_ok=True)
    events += box_entries(tracks, holders, direction, pitch_length, pitch_width, fps)
    events.sort(key=lambda e: (e.get("time", 0), e.get("type", "")))

    stats = build_match_stats(
        tracks,
        holders,
        team_ball_control,
        events,
        fps,
        video_path,
        pitch=pitch_mapper if shot_aware and shots else pitch,
        direction=direction,
    )
    
    # Add shot statistics
    if shot_aware and shots:
        stats["shots"] = {
            "total": len(shots),
            "by_type": {},
            "calibrated_shots": sum(1 for s in shots if s.pitch_calibration_valid),
            "metrics_enabled_shots": sum(1 for s in shots if s.metrics_enabled),
        }
        for shot in shots:
            shot_type = shot.shot_type.value
            stats["shots"]["by_type"][shot_type] = stats["shots"]["by_type"].get(shot_type, 0) + 1

    with open("stubs/cv_full_tracks.pkl", "wb") as f:
        pickle.dump({
            "tracks": tracks,
            "holders": holders,
            "fps": fps,
            "pitch": pitch,
            "shots": shots if shot_aware else [],
            "camera": camera
        }, f)

    with open("stats/events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, default=_json_default)
    with open("stats/match_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=_json_default)

    # Print diagnostics
    print(f"\n=== PIPELINE RESULTS ===")
    print(f"Frames: {len(video_frames)}  Duration: {len(video_frames)/fps:.1f}s")
    
    if shot_aware and shots:
        print(f"\nShots:")
        print(f"  Total shots: {len(shots)}")
        print(f"  Shot types: {stats['shots']['by_type']}")
        print(f"  Shots with valid calibration: {stats['shots']['calibrated_shots']}")
        print(f"  Shots with metrics enabled: {stats['shots']['metrics_enabled_shots']}")
    
    print(f"\nIdentities:")
    player_ids = set()
    gk_ids = set()
    for frame in tracks["players"]:
        player_ids.update(frame.keys())
    for frame in tracks["goalkeepers"]:
        gk_ids.update(frame.keys())
    print(f"  Total player IDs: {len(player_ids)}")
    print(f"  Total goalkeeper IDs: {len(gk_ids)}")
    print(f"  Players in stats sheet: {len(stats['players'])}")
    
    print(f"\nBall tracking:")
    ball_present = sum(1 for b in tracks["ball"] if b.get(1))
    ball_detected = sum(1 for b in tracks["ball"] if b.get(1, {}).get("detected"))
    ball_interp = sum(1 for b in tracks["ball"] if b.get(1, {}).get("interpolated"))
    print(f"  Frames with ball: {ball_present}/{len(tracks['ball'])} ({100*ball_present/len(tracks['ball']):.1f}%)")
    print(f"  Real detections: {ball_detected}")
    print(f"  Interpolated: {ball_interp}")
    print(f"  Missing: {len(tracks['ball']) - ball_present}")
    
    print(f"\nPossession:")
    known_poss = sum(1 for h in holders if h is not None)
    print(f"  Known holder: {known_poss}/{len(holders)} frames ({100*known_poss/len(holders):.1f}%)")
    touches_players = sum(1 for p in stats['players'] if p.get('touches', 0) > 0)
    print(f"  Players with touches: {touches_players}")
    
    print(f"\nPitch mapping:")
    if shot_aware and shots:
        mapped_players = sum(1 for frame in tracks["players"] for p in frame.values() 
                             if p.get("position_transformed") is not None and p.get("pitch_valid", False))
        total_players = sum(len(frame) for frame in tracks["players"])
        valid_frames = sum(1 for v in camera["valid"] if v)
        print(f"  Valid camera motion frames: {valid_frames}/{n_frames} ({100*valid_frames/n_frames:.1f}%)")
        if total_players > 0:
            print(f"  Players mapped (with valid calibration): {100*mapped_players/total_players:.1f}%")
    else:
        print(f"  Pitch size: {pitch_length:.1f}m × {pitch_width:.1f}m")
        mapped_players = sum(1 for frame in tracks["players"] for p in frame.values() 
                             if p.get("position_transformed") is not None)
        total_players = sum(len(frame) for frame in tracks["players"])
        if total_players > 0:
            print(f"  Players mapped: {100*mapped_players/total_players:.1f}%")
    
    print(f"\nEvents: {len(events)} total")
    print(f"  Event counts: {stats.get('event_counts')}")
    print(f"\nWrote stats/match_stats.json and stats/events.json")

    if skip_video:
        return stats

    print("\n=== GENERATING OUTPUT VIDEO ===")
    if shot_aware and shots:
        print("Using shot-aware annotation...")
        output_frames = draw_shot_aware_annotations(video_frames, tracks, team_ball_control, shots, pitch)
        output_frames = camera_estimator.draw_camera_movement(output_frames, camera)
        output_frames = draw_speed_and_distance_conditional(output_frames, tracks, shots)
    else:
        print("Using standard annotation...")
        output_frames = draw_annotations(video_frames, tracks, team_ball_control, pitch)
        output_frames = camera_estimator.draw_camera_movement(output_frames, camera)
        output_frames = speed_estimator.draw_speed_and_distance(output_frames, tracks)
    
    save_video(output_frames, "output_videos/cv_output_shot_aware.avi", fps=fps)
    print("Wrote output_videos/cv_output_shot_aware.avi")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Shot-aware football CV pipeline")
    parser.add_argument("--video", default="input_videos/arsenal-vs-everton.mp4")
    parser.add_argument("--model", default="models/best.pt")
    parser.add_argument(
        "--no-stub",
        action="store_true",
        help="Re-run YOLO even if stubs/cv_tracks.pkl exists",
    )
    parser.add_argument(
        "--skip-video",
        action="store_true",
        help="Write JSON stats only, skip annotated video",
    )
    parser.add_argument(
        "--no-shot-detection",
        action="store_true",
        help="Disable shot detection (use standard pipeline)",
    )
    args = parser.parse_args()
    run(
        video_path=args.video,
        model_path=args.model,
        read_from_stub=not args.no_stub,
        skip_video=args.skip_video,
        shot_aware=not args.no_shot_detection,
    )


if __name__ == "__main__":
    main()
