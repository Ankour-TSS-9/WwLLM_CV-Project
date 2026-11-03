import os
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.append("../")
from utils import get_center_of_bbox, get_foot_position, measure_distance

from cv import config
from cv.temporal_ball_tracker import BallCandidate, BallState, TemporalBallTracker


class ImprovedTracker:
    """YOLO + ByteTrack with goalkeepers kept separate and a single ball track."""

    def __init__(self, model_path):
        from ultralytics import YOLO
        import supervision as sv
        import warnings

        self.model = YOLO(model_path)
        self._imgsz_override = config.INFERENCE_IMGSZ  # F2: default from config
        self.ball_temporal_tracker = TemporalBallTracker()

        # F4: ByteTrack buffer from config flag
        _track_buf = config.BYTETRACK_BUFFER if config.USE_F4_BUFFER else 30
        if _track_buf != 30:
            print(f"  ByteTrack buffer: {_track_buf} frames (F4 flag)")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, message=".*ByteTrack.*deprecated.*")
            self.tracker = sv.ByteTrack(
                track_activation_threshold=config.BALL_CONF,
                lost_track_buffer=_track_buf,
            )

    def add_position_to_tracks(self, tracks):
        for object_name, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    bbox = track_info.get("bbox")
                    if not bbox:
                        continue
                    if object_name == "ball":
                        position = get_center_of_bbox(bbox)
                    else:
                        position = get_foot_position(bbox)
                    tracks[object_name][frame_num][track_id]["position"] = position

    def interpolate_ball_positions(self, ball_positions, max_gap=None):
        """Linear-fill short gaps only. Long gaps stay empty (no invented ball)."""
        max_gap = config.BALL_MAX_INTERP_GAP if max_gap is None else max_gap
        rows = []
        detected = []
        
        # Track which frames originally had real ball detections
        for frame_ball in ball_positions:
            info = frame_ball.get(1, {})
            bbox = info.get("bbox")
            has_bbox = (
                bbox is not None
                and len(bbox) == 4
                and info.get("detected", info.get("state") != BallState.PREDICTED.value)
                and not info.get("interpolated", False)
            )
            detected.append(has_bbox)
            
            if has_bbox:
                rows.append(bbox)
            else:
                rows.append([np.nan, np.nan, np.nan, np.nan])

        df = pd.DataFrame(rows, columns=["x1", "y1", "x2", "y2"])
        detected_idx = [i for i, d in enumerate(detected) if d]

        # Interpolate gaps between detected frames
        if len(detected_idx) >= 2:
            for left, right in zip(detected_idx, detected_idx[1:]):
                gap = right - left
                if not (1 < gap <= max_gap):
                    continue
                a = df.iloc[left].tolist()
                b = df.iloc[right].tolist()
                if any(v != v for v in a + b):
                    continue
                step = measure_distance(get_center_of_bbox(a), get_center_of_bbox(b)) / gap
                if step > config.BALL_MAX_STEP_PX:
                    continue
                # Fill the gap
                df.iloc[left : right + 1] = df.iloc[left : right + 1].interpolate(limit=gap)

        # Build output with correct flags
        out = []
        for i, row in df.iterrows():
            existing = ball_positions[i].get(1, {})
            if existing.get("state") == BallState.PREDICTED.value:
                out.append({1: existing})
                continue
            if row.isna().any():
                # No bbox (not detected, not interpolated)
                out.append({})
            else:
                # Has bbox: either originally detected or newly interpolated
                originally_detected = detected[i] if i < len(detected) else False
                payload = dict(existing)
                payload["bbox"] = row.tolist()
                payload["detected"] = originally_detected
                payload["interpolated"] = not originally_detected
                if not originally_detected and config.USE_TEMPORAL_BALL_TRACKING:
                    payload["state"] = BallState.INTERPOLATED.value
                out.append({1: payload})
        return out
    
    def second_pass_ball_detection(self, frames, ball_positions):
        """Second pass: detect ball in missed frames using region around last known position."""
        import supervision as sv
        
        missing_frames = []
        for frame_num in range(len(ball_positions)):
            if not ball_positions[frame_num].get(1):
                missing_frames.append(frame_num)
        
        if not missing_frames:
            return ball_positions
        
        print(f"  Second-pass attempting {len(missing_frames)} missing frames...")
        
        # Process only frames with nearby ball detections (within 15 frames)
        processed = 0
        for frame_num in missing_frames:
            # Find nearest ball detection
            prev_ball = None
            next_ball = None
            
            for i in range(frame_num - 1, max(-1, frame_num - 15), -1):
                if ball_positions[i].get(1):
                    prev_ball = ball_positions[i][1]
                    break
            
            for i in range(frame_num + 1, min(len(ball_positions), frame_num + 15)):
                if ball_positions[i].get(1):
                    next_ball = ball_positions[i][1]
                    break
            
            if not prev_ball and not next_ball:
                continue
            
            # Estimate search region
            if prev_ball and next_ball:
                prev_center = get_center_of_bbox(prev_ball["bbox"])
                next_center = get_center_of_bbox(next_ball["bbox"])
                search_center = [(prev_center[0] + next_center[0]) / 2, 
                                (prev_center[1] + next_center[1]) / 2]
            elif prev_ball:
                search_center = get_center_of_bbox(prev_ball["bbox"])
            else:
                search_center = get_center_of_bbox(next_ball["bbox"])
            
            # Create crop region (200x200 around estimated position)
            h, w = frames[frame_num].shape[:2]
            x1 = int(max(0, search_center[0] - 100))
            y1 = int(max(0, search_center[1] - 100))
            x2 = int(min(w, search_center[0] + 100))
            y2 = int(min(h, search_center[1] + 100))
            
            if x2 - x1 < 50 or y2 - y1 < 50:
                continue
            
            crop = frames[frame_num][y1:y2, x1:x2]
            
            # Run detection on crop with lower confidence
            detection = self.model.predict(crop, conf=config.BALL_CONF * 0.7, verbose=False)[0]
            if len(detection.boxes) == 0:
                continue
            
            detection_sv = sv.Detections.from_ultralytics(detection)
            cls_names = detection.names
            cls_inv = {v: k for k, v in cls_names.items()}
            # Model may use "ball" or "football" as class name
            ball_id = cls_inv.get("ball") or cls_inv.get("football")
            
            if ball_id is None:
                continue
            
            # Find ball in detections
            for i, class_id in enumerate(detection_sv.class_id):
                if int(class_id) == int(ball_id):
                    bbox_crop = detection_sv.xyxy[i].tolist()
                    # Convert crop coordinates back to frame coordinates
                    bbox = [bbox_crop[0] + x1, bbox_crop[1] + y1, 
                           bbox_crop[2] + x1, bbox_crop[3] + y1]
                    ball_positions[frame_num][1] = {
                        "bbox": bbox,
                        "conf": float(detection_sv.confidence[i]),
                        "detected": True,
                        "interpolated": False,
                        "second_pass": True
                    }
                    processed += 1
                    break
        
        print(f"  Recovered {processed} ball detections")
        return ball_positions

    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        imgsz = getattr(self, "_imgsz_override", config.INFERENCE_IMGSZ)
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(
                frames[i : i + batch_size],
                conf=(
                    config.BALL_CANDIDATE_CONF
                    if config.USE_TEMPORAL_BALL_TRACKING
                    else config.BALL_CONF
                ),
                imgsz=imgsz,
                verbose=False,
            )
            detections += detections_batch
        return detections

    def _class_lookup(self, names):
        inv = {v: k for k, v in names.items()}
        return names, inv

    def _conf_floor(self, class_name):
        if class_name in ("ball", "football"):
            if config.USE_TEMPORAL_BALL_TRACKING:
                return config.BALL_CANDIDATE_CONF
            return config.BALL_CONF
        if class_name == "goalkeeper":
            return config.GOALKEEPER_CONF
        if class_name == "referee":
            return config.REFEREE_CONF
        return config.PLAYER_CONF

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, "rb") as f:
                return pickle.load(f)

        import supervision as sv

        detections = self.detect_frames(frames)
        tracks = {
            "players": [],
            "goalkeepers": [],
            "referees": [],
            "ball": [],
        }

        prev_ball_center = None
        self.ball_temporal_tracker.reset()

        for frame_num, detection in enumerate(detections):
            cls_names, cls_inv = self._class_lookup(detection.names)
            detection_supervision = sv.Detections.from_ultralytics(detection)

            tracks["players"].append({})
            tracks["goalkeepers"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            if len(detection_supervision) == 0 and not config.USE_TEMPORAL_BALL_TRACKING:
                prev_ball_center = None
                continue

            keep = []
            for i, class_id in enumerate(detection_supervision.class_id):
                name = cls_names.get(int(class_id), "")
                conf = float(detection_supervision.confidence[i])
                keep.append(conf >= self._conf_floor(name))
            keep = np.array(keep, dtype=bool)
            filtered = detection_supervision[keep]

            # Model may use "ball" or "football" as class name
            ball_id = cls_inv.get("ball") or cls_inv.get("football")
            person_mask = np.ones(len(filtered), dtype=bool)
            if ball_id is not None and len(filtered):
                person_mask = filtered.class_id != ball_id
            people = filtered[person_mask] if len(filtered) else filtered
            tracked_people = (
                self.tracker.update_with_detections(people) if len(people) else people
            )

            for detection in tracked_people:
                bbox = detection[0].tolist()
                conf = detection[2]
                class_id = detection[3]
                track_id = detection[4]
                if track_id is None:
                    continue
                name = cls_names.get(int(class_id), "")
                payload = {
                    "bbox": bbox,
                    "conf": float(conf) if conf is not None else 0.0,
                }
                if name == "player":
                    tracks["players"][frame_num][int(track_id)] = payload
                elif name == "goalkeeper":
                    tracks["goalkeepers"][frame_num][int(track_id)] = payload
                elif name == "referee":
                    tracks["referees"][frame_num][int(track_id)] = payload

            self._assign_ball(
                filtered,
                cls_names,
                cls_inv,
                tracks,
                frame_num,
                prev_ball_center,
                self.ball_temporal_tracker,
                frames[frame_num].shape,
            )
            ball_info = tracks["ball"][frame_num].get(1)
            if ball_info and ball_info.get("bbox") and ball_info.get("detected"):
                prev_ball_center = get_center_of_bbox(ball_info["bbox"])
            elif not config.USE_TEMPORAL_BALL_TRACKING:
                prev_ball_center = None

        if stub_path is not None:
            os.makedirs(os.path.dirname(stub_path) or ".", exist_ok=True)
            with open(stub_path, "wb") as f:
                pickle.dump(tracks, f)

        return tracks

    def _assign_ball(
        self,
        detections,
        cls_names,
        cls_inv,
        tracks,
        frame_num,
        prev_center,
        temporal_tracker=None,
        frame_shape=None,
    ):
        # Model may use "ball" or "football" as class name
        ball_id = cls_inv.get("ball") or cls_inv.get("football")
        if config.USE_TEMPORAL_BALL_TRACKING and temporal_tracker is not None:
            candidates = []
            if ball_id is not None:
                for detection in detections:
                    bbox = detection[0].tolist()
                    conf = detection[2]
                    class_id = detection[3]
                    if int(class_id) != int(ball_id):
                        continue
                    confidence = float(conf) if conf is not None else 0.0
                    candidates.append(
                        BallCandidate(bbox=bbox, confidence=confidence, frame_num=frame_num)
                    )

            selected, state = temporal_tracker.process_frame(
                candidates, frame_num, frame_shape=frame_shape
            )
            if selected is not None:
                tracks["ball"][frame_num][1] = {
                    "bbox": selected.bbox,
                    "conf": selected.confidence,
                    "detected": state == BallState.DETECTED,
                    "interpolated": False,
                    "state": state.value,
                }
            elif state == BallState.PREDICTED:
                trajectory = temporal_tracker.trajectory
                center = trajectory.predict_position(frame_num)
                last_bbox = trajectory.last_detected_bbox
                if center is not None and last_bbox is not None:
                    width = last_bbox[2] - last_bbox[0]
                    height = last_bbox[3] - last_bbox[1]
                    tracks["ball"][frame_num][1] = {
                        "bbox": [
                            float(center[0] - width / 2),
                            float(center[1] - height / 2),
                            float(center[0] + width / 2),
                            float(center[1] + height / 2),
                        ],
                        "conf": None,
                        "detected": False,
                        "interpolated": False,
                        "state": state.value,
                    }
            return

        if ball_id is None or len(detections) == 0:
            return

        candidates = []
        for detection in detections:
            bbox = detection[0].tolist()
            conf = detection[2]
            class_id = detection[3]
            if int(class_id) != int(ball_id):
                continue
            center = get_center_of_bbox(bbox)
            score = float(conf) if conf is not None else 0.0
            if prev_center is not None:
                dist = np.hypot(center[0] - prev_center[0], center[1] - prev_center[1])
                score = max(0.0, score - 0.001 * dist)
            candidates.append((score, bbox, float(conf) if conf is not None else 0.0))

        if not candidates:
            return

        _, bbox, conf = max(candidates, key=lambda x: x[0])
        tracks["ball"][frame_num][1] = {
            "bbox": bbox,
            "conf": conf,
            "detected": True,
            "interpolated": False,
        }
