"""
pose_track.py  —  webcam body joint tracker
Uses mediapipe >= 0.10 Tasks API (not the old mp.solutions API).

SETUP:
  pip install opencv-python mediapipe

  Download the model (~3 MB) before running:
  curl -L -o pose_landmarker.task \
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

RUN:
  python pose_track.py               # looks for pose_landmarker.task in cwd
  python pose_track.py path/to/model.task

Press Q to quit.
"""

import sys
import time
import pathlib

import cv2
import numpy as np

from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarkerResult,
    PoseLandmark,
    PoseLandmarksConnections,
)
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
import mediapipe as mp

# ── Colours (BGR) ────────────────────────────────────────
GREEN  = (0, 230, 120)
PURPLE = (210, 80, 240)
ORANGE = (30, 160, 255)
CYAN   = (220, 210, 60)
WHITE  = (240, 240, 240)
GRAY   = (100, 100, 110)
RED    = (50,  50, 220)
BLACK  = (0, 0, 0)

# ── Angle helper ──────────────────────────────────────────
def angle_at(a, b, c):
    """Angle in degrees at vertex B, given three (x,y) points."""
    ba = np.array(a, float) - np.array(b, float)
    bc = np.array(c, float) - np.array(b, float)
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n < 1e-6:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(ba, bc) / n, -1.0, 1.0))))


# ── Pixel coordinate from normalised landmark ─────────────
def px(lm, idx, w, h):
    p = lm[idx]
    return int(p.x * w), int(p.y * h)


# ── Draw skeleton from PoseLandmarksConnections ───────────
def draw_skeleton(frame, lm, w, h):
    for conn in PoseLandmarksConnections.POSE_LANDMARKS:
        a = px(lm, conn.start, w, h)
        b = px(lm, conn.end,   w, h)
        cv2.line(frame, a, b, (55, 55, 75), 1, cv2.LINE_AA)
    for i in range(len(lm)):
        cv2.circle(frame, px(lm, i, w, h), 3, (70, 70, 95), -1, cv2.LINE_AA)


# ── Draw annotated joint with arc + label ─────────────────
def draw_joint(frame, a, b, c, label, angle_deg, colour):
    # limb lines
    cv2.line(frame, a, b, colour, 2, cv2.LINE_AA)
    cv2.line(frame, b, c, colour, 2, cv2.LINE_AA)

    # joint dot
    cv2.circle(frame, b, 7, colour, -1, cv2.LINE_AA)
    cv2.circle(frame, b, 9, WHITE,  1,  cv2.LINE_AA)

    # small arc
    ang1 = float(np.degrees(np.arctan2(a[1]-b[1], a[0]-b[0])))
    ang2 = float(np.degrees(np.arctan2(c[1]-b[1], c[0]-b[0])))
    cv2.ellipse(frame, b, (20, 20), 0, ang1, ang2, colour, 1, cv2.LINE_AA)

    # label background + text
    text = f"{label} {angle_deg:.0f}'"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
    tx, ty = b[0] + 12, b[1] - 10
    cv2.rectangle(frame, (tx-2, ty-th-3), (tx+tw+2, ty+3), (10,10,20), -1)
    cv2.putText(frame, text, (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, colour, 1, cv2.LINE_AA)


# ── Right-side panel with angle bars ─────────────────────
def draw_panel(frame, rows, h):
    PANEL_W = 215
    fw = frame.shape[1]

    # semi-transparent dark background
    roi = frame[:, fw-PANEL_W:]
    overlay = roi.copy()
    overlay[:] = (16, 16, 26)
    cv2.addWeighted(overlay, 0.80, roi, 0.20, 0, roi)
    cv2.line(frame, (fw-PANEL_W, 0), (fw-PANEL_W, h), GRAY, 1)

    cv2.putText(frame, "JOINT ANGLES", (fw-PANEL_W+10, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, WHITE, 1, cv2.LINE_AA)
    cv2.line(frame, (fw-PANEL_W+10, 33), (fw-10, 33), GRAY, 1)

    y = 58
    for label, val, colour in rows:
        bx, by = fw-PANEL_W+10, y+2
        bw, bh = PANEL_W-24, 7
        cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), (38,38,52), -1)
        fill = int(np.clip(val/180.0, 0, 1) * bw)
        cv2.rectangle(frame, (bx, by), (bx+fill, by+bh), colour, -1)

        cv2.putText(frame, label, (bx, y-1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, colour, 1, cv2.LINE_AA)
        cv2.putText(frame, f"{val:5.1f}deg", (fw-78, y-1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, WHITE, 1, cv2.LINE_AA)
        y += 36

    cv2.putText(frame, "Q  quit", (fw-PANEL_W+10, h-12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, GRAY, 1, cv2.LINE_AA)


# ── Main ──────────────────────────────────────────────────
def main():
    # Locate model
    model_path = sys.argv[1] if len(sys.argv) > 1 else "pose_landmarker.task"
    if not pathlib.Path(model_path).exists():
        print(f"ERROR: model not found at '{model_path}'")
        print()
        print("Download it with:")
        print('  curl -L -o pose_landmarker.task \\')
        print('    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/'
              'pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"')
        sys.exit(1)

    # PoseLandmarker in VIDEO mode — synchronous, frame-by-frame
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.50,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: cannot open webcam (index 0).")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    LM = PoseLandmark
    start_ms = int(time.time() * 1000)

    with PoseLandmarker.create_from_options(options) as landmarker:
        print("Running — press Q to quit.")
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)      # mirror so it feels like a mirror
            h, w = frame.shape[:2]

            # Timestamp for VIDEO mode (must be monotonically increasing)
            timestamp_ms = int(time.time() * 1000) - start_ms

            # Run detection
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
            )
            result: PoseLandmarkerResult = landmarker.detect_for_video(mp_image, timestamp_ms)

            # Darken background slightly so overlays pop
            cv2.addWeighted(frame, 0.6, np.zeros_like(frame), 0.4, 0, frame)

            if result.pose_landmarks:
                lm = result.pose_landmarks[0]   # first (only) pose

                draw_skeleton(frame, lm, w, h)

                # Helper: landmark → pixel, clamped to frame
                def p(idx): return px(lm, idx, w, h)

                # ── Compute angles for key PT joints ──────
                l_sh  = angle_at(p(LM.LEFT_HIP),      p(LM.LEFT_SHOULDER),  p(LM.LEFT_WRIST))
                r_sh  = angle_at(p(LM.RIGHT_HIP),     p(LM.RIGHT_SHOULDER), p(LM.RIGHT_WRIST))
                l_el  = angle_at(p(LM.LEFT_SHOULDER),  p(LM.LEFT_ELBOW),    p(LM.LEFT_WRIST))
                r_el  = angle_at(p(LM.RIGHT_SHOULDER), p(LM.RIGHT_ELBOW),   p(LM.RIGHT_WRIST))
                l_kn  = angle_at(p(LM.LEFT_HIP),      p(LM.LEFT_KNEE),      p(LM.LEFT_ANKLE))
                r_kn  = angle_at(p(LM.RIGHT_HIP),     p(LM.RIGHT_KNEE),     p(LM.RIGHT_ANKLE))
                l_hip = angle_at(p(LM.LEFT_SHOULDER),  p(LM.LEFT_HIP),      p(LM.LEFT_KNEE))
                r_hip = angle_at(p(LM.RIGHT_SHOULDER), p(LM.RIGHT_HIP),     p(LM.RIGHT_KNEE))

                # ── Draw annotated joints ──────────────────
                draw_joint(frame, p(LM.LEFT_HIP),       p(LM.LEFT_SHOULDER),  p(LM.LEFT_WRIST),   "L.Sh", l_sh,  GREEN)
                draw_joint(frame, p(LM.RIGHT_HIP),      p(LM.RIGHT_SHOULDER), p(LM.RIGHT_WRIST),  "R.Sh", r_sh,  GREEN)
                draw_joint(frame, p(LM.LEFT_SHOULDER),  p(LM.LEFT_ELBOW),     p(LM.LEFT_WRIST),   "L.El", l_el,  PURPLE)
                draw_joint(frame, p(LM.RIGHT_SHOULDER), p(LM.RIGHT_ELBOW),    p(LM.RIGHT_WRIST),  "R.El", r_el,  PURPLE)
                draw_joint(frame, p(LM.LEFT_HIP),       p(LM.LEFT_KNEE),      p(LM.LEFT_ANKLE),   "L.Kn", l_kn,  ORANGE)
                draw_joint(frame, p(LM.RIGHT_HIP),      p(LM.RIGHT_KNEE),     p(LM.RIGHT_ANKLE),  "R.Kn", r_kn,  ORANGE)

                # ── Sidebar panel ──────────────────────────
                draw_panel(frame, [
                    ("L shoulder elev", l_sh,  GREEN),
                    ("R shoulder elev", r_sh,  GREEN),
                    ("L elbow flex",    l_el,  PURPLE),
                    ("R elbow flex",    r_el,  PURPLE),
                    ("L knee flex",     l_kn,  ORANGE),
                    ("R knee flex",     r_kn,  ORANGE),
                    ("L hip flex",      l_hip, CYAN),
                    ("R hip flex",      r_hip, CYAN),
                ], h)

            else:
                cv2.putText(frame, "no person detected", (30, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, RED, 2, cv2.LINE_AA)

            cv2.imshow("Pose Tracker", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
