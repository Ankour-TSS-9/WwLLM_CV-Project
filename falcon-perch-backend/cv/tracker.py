import os
import pickle
import time
import sys
from bisect import bisect_left

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
        self._classify_ball_flight(tracks)

    def _classify_ball_flight(self, tracks):
        ball_frames = tracks.get("ball") or []
        if not ball_frames:
            return

        player_frames = tracks.get("players") or []
        goalkeeper_frames = tracks.get("goalkeepers") or []
        player_heights = []
        for object_tracks in player_frames + goalkeeper_frames:
            for player in object_tracks.values():
                bbox = player.get("bbox")
                if bbox and len(bbox) == 4 and bbox[3] > bbox[1]:
                    player_heights.append(bbox[3] - bbox[1])
        reference_height = float(np.median(player_heights)) if player_heights else 40.0

        direct_indices = []
        direct_modes = {}
        vertical_positions = {}
        for frame_num, frame_ball in enumerate(ball_frames):
            info = frame_ball.get(1)
            bbox = info.get("bbox") if info else None
            if not bbox or len(bbox) != 4:
                continue
            vertical_positions[frame_num] = (bbox[1] + bbox[3]) / 2.0
            is_direct = (
                info.get("detected", info.get("state") != BallState.PREDICTED.value)
                and not info.get("interpolated", False)
                and info.get("state") != BallState.PREDICTED.value
            )
            if is_direct:
                direct_indices.append(frame_num)

        for frame_num in direct_indices:
            info = ball_frames[frame_num][1]
            bbox = info["bbox"]
            ball_x = (bbox[0] + bbox[2]) / 2.0
            ball_y = (bbox[1] + bbox[3]) / 2.0
            ball_bottom = bbox[3]
            local_players = []
            if frame_num < len(player_frames):
                local_players.extend(player_frames[frame_num].values())
            if frame_num < len(goalkeeper_frames):
                local_players.extend(goalkeeper_frames[frame_num].values())

            insertion = bisect_left(direct_indices, frame_num)
            previous = direct_indices[insertion - 1] if insertion > 0 else None
            next_frame = (
                direct_indices[insertion + 1]
                if insertion + 1 < len(direct_indices)
                else None
            )
            prior = previous if previous is not None and frame_num - previous <= 3 else None
            following = next_frame if next_frame is not None and next_frame - frame_num <= 3 else None

            confidence = 0.0
            ground_confidence = 0.0
            for player in local_players:
                player_bbox = player.get("bbox")
                if not player_bbox or len(player_bbox) != 4:
                    continue
                player_height = max(1.0, player_bbox[3] - player_bbox[1])
                foot_distance = np.hypot(
                    ball_x - (player_bbox[0] + player_bbox[2]) / 2.0,
                    ball_bottom - player_bbox[3],
                ) / player_height
                if foot_distance <= 0.50:
                    ground_confidence = max(ground_confidence, 0.75)

                horizontal_gap = max(
                    player_bbox[0] - ball_x,
                    0.0,
                    ball_x - player_bbox[2],
                )
                vertical_gap = max(player_bbox[1] - ball_y, 0.0, ball_y - player_bbox[3])
                relative_distance = np.hypot(horizontal_gap, vertical_gap) / player_height
                if relative_distance > 2.0:
                    continue

                lift_ratio = (player_bbox[3] - ball_bottom) / player_height
                if lift_ratio > 2.0 and relative_distance < 2.5:
                    confidence = max(confidence, 0.95)
                elif prior is not None and following is not None and lift_ratio > 0.25:
                    prior_step = (
                        vertical_positions[frame_num] - vertical_positions[prior]
                    ) / (frame_num - prior)
                    following_step = (
                        vertical_positions[following] - vertical_positions[frame_num]
                    ) / (following - frame_num)
                    if (
                        prior_step * following_step > 0
                        and abs(prior_step) > 0.20 * player_height
                        and abs(following_step) > 0.20 * player_height
                    ):
                        confidence = max(confidence, 0.70)

            if prior is not None and following is not None:
                prior_rise = (
                    vertical_positions[prior] - vertical_positions[frame_num]
                ) / (frame_num - prior)
                following_fall = (
                    vertical_positions[following] - vertical_positions[frame_num]
                ) / (following - frame_num)
                arc_height = (
                    vertical_positions[prior] + vertical_positions[following]
                ) / 2.0 - vertical_positions[frame_num]
                if (
                    arc_height > max(5.0, 0.18 * reference_height)
                    and prior_rise > 0.12 * reference_height
                    and following_fall > 0.12 * reference_height
                ):
                    confidence = max(confidence, 0.82)

            if confidence > 0:
                direct_modes[frame_num] = ("airborne", confidence)
            elif ground_confidence > 0:
                direct_modes[frame_num] = ("ground", ground_confidence)
            else:
                direct_modes[frame_num] = ("unknown", 0.0)

        for frame_num, frame_ball in enumerate(ball_frames):
            info = frame_ball.get(1)
            if not info or not info.get("bbox"):
                continue
            if frame_num in direct_modes:
                mode, confidence = direct_modes[frame_num]
            else:
                insertion = bisect_left(direct_indices, frame_num)
                nearby = direct_indices[max(0, insertion - 1):insertion + 1]
                closest = min(
                    (index for index in nearby if abs(index - frame_num) <= 6),
                    key=lambda index: abs(index - frame_num),
                    default=None,
                )
                if closest is None:
                    mode, confidence = "unknown", 0.0
                else:
                    mode, source_confidence = direct_modes[closest]
                    confidence = source_confidence * 0.8 if mode == "airborne" else 0.0

            info["ball_mode"] = mode
            info["airborne_confidence"] = round(confidence, 3)

    def interpolate_ball_positions(self, ball_positions, max_gap=None, camera_cuts=None):
        """Linear-fill short gaps only. Long gaps stay empty (no invented ball)."""
        max_gap = config.BALL_MAX_INTERP_GAP if max_gap is None else max_gap
        camera_cut_set = set(camera_cuts or ())
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
                if any(left < cut <= right for cut in camera_cut_set):
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

    def suppress_out_of_frame_predictions(self, ball_positions, frames):
        """Drop a predicted run once it exits the image, until a real detection returns."""
        suppressing_run = False
        reset_frames = []
        for frame_num, frame_ball in enumerate(ball_positions):
            info = frame_ball.get(1)
            if not info:
                continue
            if info.get("detected") and info.get("state") != BallState.PREDICTED.value:
                suppressing_run = False
                continue
            if info.get("state") != BallState.PREDICTED.value:
                continue

            height, width = frames[frame_num].shape[:2]
            bbox = info.get("bbox")
            if not bbox or len(bbox) != 4:
                out_of_frame = True
            else:
                center_x = (bbox[0] + bbox[2]) / 2.0
                center_y = (bbox[1] + bbox[3]) / 2.0
                out_of_frame = not (0 <= center_x < width and 0 <= center_y < height)

            if out_of_frame and not suppressing_run:
                reset_frames.append(frame_num)
                suppressing_run = True
            if suppressing_run:
                frame_ball.pop(1, None)

        return reset_frames
    
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
        total_batches = (len(frames) + batch_size - 1) // batch_size
        started_at = time.monotonic()
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
            batch_number = i // batch_size + 1
            if batch_number % 10 == 0 or batch_number == total_batches:
                processed_frames = min(i + batch_size, len(frames))
                elapsed = time.monotonic() - started_at
                print(
                    f"  Object detection: batch {batch_number}/{total_batches} "
                    f"({processed_frames}/{len(frames)} frames, {elapsed:.1f}s elapsed)",
                    flush=True,
                )
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

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None, camera_cuts=None):
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
        camera_cut_set = set(camera_cuts or ())

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
                frame_num in camera_cut_set,
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
        is_camera_cut=False,
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
                candidates,
                frame_num,
                is_camera_cut=is_camera_cut,
                frame_shape=frame_shape,
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
                    if frame_shape is not None:
                        frame_height, frame_width = frame_shape[:2]
                        if not (
                            0 <= center[0] < frame_width
                            and 0 <= center[1] < frame_height
                        ):
                            temporal_tracker.reset()
                            return
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
