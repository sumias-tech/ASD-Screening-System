# scoring.py
import math

# Module-level state for tracking wrist positions across frames
_prev_left_wrist  = None
_prev_right_wrist = None
_first_frame      = True   # skip movement score on the very first frame


def reset_tracking():
    """Call this at the start of every new video to clear inter-frame state."""
    global _prev_left_wrist, _prev_right_wrist, _first_frame
    _prev_left_wrist  = None
    _prev_right_wrist = None
    _first_frame      = True


def calculate_score(landmarks):

    global _prev_left_wrist, _prev_right_wrist, _first_frame

    if landmarks is None:
        return {
            "eye_contact": 0,
            "attention":   0,
            "movement":    0,
            "asd_score":   0,
            "risk":        "Unknown"
        }

    # ── FACE DIRECTION ────────────────────────────────────────────────────
    # Measures nose symmetry relative to the eyes — not screen position.
    # A face looking straight at the camera has equal nose-to-eye distances.
    nose      = landmarks[0]
    left_eye  = landmarks[2]
    right_eye = landmarks[5]

    left_dist  = abs(nose.x - left_eye.x)
    right_dist = abs(nose.x - right_eye.x)
    symmetry   = abs(left_dist - right_dist)

    # Symmetry near 0 = facing forward. Scale: 0.05 diff → score drops ~20pts.
    face_direction = max(0, min(100, 100 - symmetry * 400))

    # ── HEAD POSE ─────────────────────────────────────────────────────────
    # Eye height difference detects head tilt / looking away.
    # A level head has both eyes at nearly equal Y.
    eye_height_diff = abs(left_eye.y - right_eye.y)

    # Scale: 0.05 diff → score drops ~20pts.
    head_pose = max(0, min(100, 100 - eye_height_diff * 400))

    # ── BODY POSTURE ──────────────────────────────────────────────────────
    left_shoulder  = landmarks[11]
    right_shoulder = landmarks[12]

    shoulder_diff = abs(left_shoulder.y - right_shoulder.y)

    # Scale: 0.1 diff → score drops ~20pts.
    body_posture = max(0, min(100, 100 - shoulder_diff * 200))

    # ── REPETITIVE HAND MOVEMENT ──────────────────────────────────────────
    # Tracks wrist velocity across consecutive sampled frames.
    # High velocity or high frequency = potential stimming behavior.
    left_wrist  = landmarks[15]
    right_wrist = landmarks[16]

    if _first_frame or _prev_left_wrist is None:
        # First frame: no previous position to compare — skip movement penalty
        movement_score = 100
        _first_frame   = False
    else:
        left_move = math.hypot(
            left_wrist.x  - _prev_left_wrist.x,
            left_wrist.y  - _prev_left_wrist.y
        )
        right_move = math.hypot(
            right_wrist.x - _prev_right_wrist.x,
            right_wrist.y - _prev_right_wrist.y
        )

        avg_move = (left_move + right_move) / 2

        # Scale: 0.05 delta per sampled frame = moderate movement → ~80pts
        #        0.25 delta (rapid flapping)  → ~0pts
        # Multiplier 400 is more realistic than 800 for 5-frame sampling.
        movement_score = max(0, min(100, 100 - avg_move * 400))

    _prev_left_wrist  = left_wrist
    _prev_right_wrist = right_wrist

    # ── ADOS-INSPIRED ATTENTION ───────────────────────────────────────────
    # Combines face direction + head pose (both relate to social attention).
    attention = (face_direction + head_pose) / 2

    # ── FINAL ASD SCORE ───────────────────────────────────────────────────
    # Equal weight to attention, posture, and repetitive movement.
    asd_score = (attention + body_posture + movement_score) / 3

    # ── RISK LEVEL ────────────────────────────────────────────────────────
    if asd_score >= 70:
        risk = "High"
    elif asd_score >= 40:
        risk = "Moderate"
    else:
        risk = "Low"

    return {
        "eye_contact": round(face_direction, 2),
        "attention":   round(attention, 2),
        "movement":    round(movement_score, 2),
        "asd_score":   round(asd_score, 2),
        "risk":        risk
    }