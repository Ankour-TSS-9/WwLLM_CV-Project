"""
Configuration parameters for the CV pipeline.
"""

# Detection confidence thresholds
PLAYER_CONF = 0.25
GOALKEEPER_CONF = 0.25
BALL_CONF = 0.12
REFEREE_CONF = 0.25

# Identity stitching
MIN_TRACK_S = 1.2           # Minimum track duration to keep (seconds)
STITCH_DIST_PX = 150        # Maximum distance to stitch tracklets (pixels)
STITCH_GAP_S = 1.2          # Maximum time gap to stitch (seconds)

# Stitching bonuses/penalties
STITCH_SAME_ROLE_BONUS = -20     # Bonus for same role (player/goalkeeper)
STITCH_DIFF_ROLE_PENALTY = 50    # Penalty for different roles
STITCH_SAME_TEAM_BONUS = -30     # Bonus for same team

# Ball tracking (baseline)
BALL_MAX_INTERP_GAP = 5          # Maximum frames to interpolate
BALL_MAX_STEP_PX = 100           # Maximum movement per frame

# Ball tracking (temporal tracker)
BALL_MIN_WIDTH_PX = 3            # Minimum ball width (from Phase D audit)
BALL_MAX_WIDTH_PX = 25           # Maximum ball width
BALL_MIN_HEIGHT_PX = 3           # Minimum ball height
BALL_MAX_HEIGHT_PX = 25          # Maximum ball height
BALL_MIN_ASPECT_RATIO = 0.5      # Minimum width/height ratio
BALL_MAX_ASPECT_RATIO = 1.5      # Maximum width/height ratio

# Temporal tracking
BALL_MEASUREMENT_NOISE = 3.0     # Detection position uncertainty (pixels)
BALL_MAX_PREDICTION_FRAMES = 10  # Max frames to predict without detection

# Pitch
PITCH_LENGTH = 105.0        # Standard pitch length (meters)
PITCH_WIDTH = 68.0          # Standard pitch width (meters)
PLAYER_HEIGHT_M = 1.75      # Assumed average player height (meters), used for scale estimation

# Speed estimation
SPEED_FRAME_WINDOW = 5          # Frame window for speed calculation
MAX_PLAYER_KMH = 36.0           # Maximum plausible player speed (km/h)
MAX_BALL_KMH = 150.0            # Maximum plausible ball speed (km/h)
MAX_STEP_M = 4.0                # Maximum step distance per frame (meters)

# Event detection
SPRINT_KMH = 20.0               # Minimum speed to count as sprint (km/h)
SPRINT_MIN_S = 1.0              # Minimum sprint duration (seconds)
SPRINT_COOLDOWN_S = 2.0         # Cooldown between sprint events (seconds)
SHOT_BALL_KMH = 30.0            # Minimum ball speed to classify as shot (km/h)
CLEARANCE_BALL_KMH = 25.0       # Minimum ball speed to classify as clearance (km/h)

# Pass / carry detection
CARRY_MIN_PLAYER_TRAVEL_M = 3.0     # Minimum carry distance in metric space (meters)
CARRY_MIN_PLAYER_TRAVEL_PX = 40.0   # Minimum carry distance in pixel space
PASS_MIN_BALL_TRAVEL_M = 5.0        # Minimum ball travel for a pass (meters)
PASS_MIN_BALL_TRAVEL_PX = 60.0      # Minimum ball travel for a pass (pixels)
PASS_MAX_GAP_S = 3.0                # Maximum time gap between pass start/end (seconds)

# Possession
POSSESSION_MAX_DIST_M = 3.0         # Maximum distance to assign possession (meters)
POSSESSION_MAX_DIST_PX = 60.0       # Maximum distance to assign possession (pixels)
POSSESSION_CLOSE_DIST_M = 1.5       # Distance considered "in control" (meters)
POSSESSION_CLOSE_DIST_PX = 30.0     # Distance considered "in control" (pixels)
POSSESSION_MIN_HOLD_S = 0.2         # Minimum seconds to register possession hold
POSSESSION_LOST_S = 0.5             # Seconds without contact to lose possession

# Pressure / tactics
PRESSURE_RADIUS_M = 5.0             # Radius for pressure event detection (meters)
PRESSURE_RADIUS_PX = 80.0           # Radius for pressure event detection (pixels)

# Stats
MIN_STATS_S = 1.0                   # Minimum seconds a player must be visible to appear in stats

# ORB GMC (Phase E1 — approved, feature-flagged)
ORB_MAX_FEATURES  = 1200   # Maximum ORB keypoints per frame
ORB_MIN_MATCHES   = 15     # Minimum raw matches to attempt affine estimation
ORB_TOP_MATCHES   = 80     # Take only the N best matches by descriptor distance
ORB_MIN_INLIERS   = 12     # Minimum RANSAC inliers to accept the estimate
ORB_MAX_DELTA_PX  = 50.0   # Sanity clamp: reject translations > this many px
ORB_MIN_DELTA_PX  = 1.0    # Sub-pixel noise gate: zero out if both axes < this
ORB_RANSAC_CONF   = 0.995  # RANSAC confidence
ORB_RANSAC_THRESH = 3.0    # RANSAC reprojection threshold (px)

# -----------------------------------------------------------------------
# Phase F feature flags — each independently configurable
# Change here; do not modify production logic directly.
# -----------------------------------------------------------------------

# F1: ORB GMC — approved (Phase E1.5: identical speed output, 11% faster, 0 failures)
USE_ORB_GMC = True          # True = ORB, False = Lucas-Kanade (original baseline)

# F2: Inference resolution — approved (Phase F: +30.9pp ball detection, +38pp possession)
INFERENCE_IMGSZ = 1280      # 640 (original baseline) | 1280 (approved, +70% runtime)

# F3: Identity stitching thresholds — REJECTED (created 14 new gaps, lost 13 player IDs)
# Baseline 150px/1.2s preserved. Do not widen without a surgical per-gap approach.
STITCH_DIST_PX_F3 = 150     # 150 (baseline, keep)
STITCH_GAP_S_F3   = 1.2     # 1.2 (baseline, keep)
USE_F3_STITCH     = False   # REJECTED — do not enable

# F4: ByteTrack buffer — REJECTED (negligible benefit, 1 new gap)
BYTETRACK_BUFFER  = 30      # 30 (baseline, keep)
USE_F4_BUFFER     = False   # REJECTED — do not enable
