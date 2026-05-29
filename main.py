import sys
import time
import pathlib
import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker, PoseLandmarkerOptions, PoseLandmarkerResult, 
    PoseLandmarksConnections, PoseLandmark
)
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

# ── Colours (BGR) ────────────────────────────────────────
GREEN  = (0, 230, 120)
PURPLE = (210, 80, 240)
ORANGE = (30, 160, 255)
CYAN   = (220, 210, 60)
WHITE  = (240, 240, 240)
GRAY   = (100, 100, 110)
RED    = (50,  50, 220)

# ── Helpers ──────────────────────────────────────────────
def angle_at(a, b, c):
    ba = np.array(a, float) - np.array(b, float)
    bc = np.array(c, float) - np.array(b, float)
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n < 1e-6: return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(ba, bc) / n, -1.0, 1.0))))

def px(lm, idx, w, h):
    p = lm[idx]
    return int(p.x * w), int(p.y * h)

def draw_skeleton(frame, lm, w, h):
    for conn in PoseLandmarksConnections.POSE_LANDMARKS:
        a = px(lm, conn.start, w, h)
        b = px(lm, conn.end,   w, h)
        cv2.line(frame, a, b, (55, 55, 75), 1, cv2.LINE_AA)
    for i in range(len(lm)):
        cv2.circle(frame, px(lm, i, w, h), 3, (70, 70, 95), -1, cv2.LINE_AA)

def draw_joint(frame, a, b, c, label, angle_deg, colour):
    cv2.line(frame, a, b, colour, 2, cv2.LINE_AA)
    cv2.line(frame, b, c, colour, 2, cv2.LINE_AA)
    cv2.circle(frame, b, 7, colour, -1, cv2.LINE_AA)
    cv2.circle(frame, b, 9, WHITE,  1,  cv2.LINE_AA)
    text = f"{label} {angle_deg:.0f}'"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
    tx, ty = b[0] + 12, b[1] - 10
    cv2.rectangle(frame, (tx-2, ty-th-3), (tx+tw+2, ty+3), (10,10,20), -1)
    cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.48, colour, 1, cv2.LINE_AA)

def draw_panel(frame, rows, h, reps, state_msg, progress, deviation):
    PANEL_W = 230
    fw = frame.shape[1]
    roi = frame[:, fw-PANEL_W:]
    overlay = roi.copy()
    overlay[:] = (16, 16, 26)
    cv2.addWeighted(overlay, 0.80, roi, 0.20, 0, roi)
    cv2.line(frame, (fw-PANEL_W, 0), (fw-PANEL_W, h), GRAY, 1)

    # Status Header
    cv2.putText(frame, f"REPS: {reps}", (fw-PANEL_W+10, 36), cv2.FONT_HERSHEY_DUPLEX, 1.2, GREEN, 2, cv2.LINE_AA)
    
    # Form UI
    cv2.putText(frame, f"PHASE: {state_msg}", (fw-PANEL_W+10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, CYAN, 1, cv2.LINE_AA)
    
    prog_col = GREEN if progress > 0.75 else WHITE
    cv2.putText(frame, f"PROG:  {int(progress*100)}%", (fw-PANEL_W+10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, prog_col, 1, cv2.LINE_AA)
    
    dev_col = RED if deviation > 30 else WHITE
    cv2.putText(frame, f"DEV:   {int(deviation)} deg", (fw-PANEL_W+10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, dev_col, 1, cv2.LINE_AA)
    
    cv2.line(frame, (fw-PANEL_W+10, 115), (fw-10, 115), GRAY, 1)

    y = 140
    for label, val, colour in rows:
        bx, by = fw-PANEL_W+10, y+2
        bw, bh = PANEL_W-24, 7
        cv2.rectangle(frame, (bx, by), (bx+bw, by+bh), (38,38,52), -1)
        fill = int(np.clip(val/180.0, 0, 1) * bw)
        cv2.rectangle(frame, (bx, by), (bx+fill, by+bh), colour, -1)
        cv2.putText(frame, label, (bx, y-1), cv2.FONT_HERSHEY_SIMPLEX, 0.42, colour, 1, cv2.LINE_AA)
        cv2.putText(frame, f"{val:5.1f}'", (fw-60, y-1), cv2.FONT_HERSHEY_SIMPLEX, 0.42, WHITE, 1, cv2.LINE_AA)
        y += 36

# ── New Keyframe State Machine ─────────────────────────────
class KeyframeRepCounter:
    def __init__(self, template_path):
        data = np.load(template_path)
        self.start_state = data['start']
        self.peak_state = data['peak']
        
        # Calculate the mathematical vector from Start -> Peak
        self.movement_vector = self.peak_state - self.start_state
        self.vector_sq_length = np.dot(self.movement_vector, self.movement_vector)
        
        if self.vector_sq_length < 1e-5:
            print("WARNING: Start and Peak states are identical. Re-record template.")
            self.vector_sq_length = 1e-5
            
        self.phase = 0       # 0: Need Start, 1: Need Peak, 2: Need Return
        self.rep_count = 0
        self.progress = 0.0
        self.deviation = 0.0

    def update(self, live_angles):
        live = np.array(live_angles)
        
        # 1. Calculate Progress (Projection of live position onto the movement vector)
        w = live - self.start_state
        self.progress = np.dot(w, self.movement_vector) / self.vector_sq_length
        self.progress = np.clip(self.progress, 0.0, 1.2) # Cap for UI readability
        
        # 2. Calculate Deviation (How far off the correct track the user's form is)
        expected_angles = self.start_state + (self.progress * self.movement_vector)
        self.deviation = np.mean(np.abs(live - expected_angles))
        
        state_msg = "POOR FORM"
        
        # Only allow state transitions if the user is performing the exercise correctly
        if self.deviation < 35.0:  # Allow 35 degrees average joint wiggle room
            if self.phase == 0:
                state_msg = "ALIGN TO START"
                if self.progress < 0.25:
                    self.phase = 1 # User is at the start
            elif self.phase == 1:
                state_msg = "GO DOWN"
                if self.progress > 0.40:
                    self.phase = 2 # User hit the bottom of the squat!
            elif self.phase == 2:
                state_msg = "COME UP"
                if self.progress < 0.25:
                    self.rep_count += 1
                    self.phase = 1 # Reset for next rep
                    
        return self.rep_count, state_msg, self.progress, self.deviation

# ── Main Runtime Loop ──────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python main_dtw.py <path_to_template.npz>")
        sys.exit(1)
        
    rep_detector = KeyframeRepCounter(sys.argv[1])

    model_path = "pose_landmarker.task"
    if not pathlib.Path(model_path).exists():
        print(f"ERROR: '{model_path}' not found.")
        sys.exit(1)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_poses=1,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    start_ms = int(time.time() * 1000)

    with PoseLandmarker.create_from_options(options) as landmarker:
        LM = PoseLandmark
        
        while True:
            ok, frame = cap.read()
            if not ok: break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            timestamp_ms = int(time.time() * 1000) - start_ms

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            cv2.addWeighted(frame, 0.6, np.zeros_like(frame), 0.4, 0, frame)

            if result.pose_landmarks:
                lm = result.pose_landmarks[0]
                draw_skeleton(frame, lm, w, h)

                def p(idx): return px(lm, idx, w, h)
                def coords(idx): return (lm[idx].x, lm[idx].y) 

                live_angles = [
                    angle_at(coords(LM.LEFT_HIP),      coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_WRIST)),
                    angle_at(coords(LM.RIGHT_HIP),     coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_WRIST)),
                    angle_at(coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_ELBOW),    coords(LM.LEFT_WRIST)),
                    angle_at(coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_ELBOW),   coords(LM.RIGHT_WRIST)),
                    angle_at(coords(LM.LEFT_HIP),      coords(LM.LEFT_KNEE),      coords(LM.LEFT_ANKLE)),
                    angle_at(coords(LM.RIGHT_HIP),     coords(LM.RIGHT_KNEE),     coords(LM.RIGHT_ANKLE)),
                    angle_at(coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_HIP),      coords(LM.LEFT_KNEE)),
                    angle_at(coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_HIP),     coords(LM.RIGHT_KNEE))
                ]

                # Run Keyframe Engine
                total_reps, state_msg, prog, dev = rep_detector.update(live_angles)

                draw_joint(frame, p(LM.LEFT_HIP),       p(LM.LEFT_SHOULDER),  p(LM.LEFT_WRIST),   "L.Sh", live_angles[0], GREEN)
                draw_joint(frame, p(LM.RIGHT_HIP),      p(LM.RIGHT_SHOULDER), p(LM.RIGHT_WRIST),  "R.Sh", live_angles[1], GREEN)
                draw_joint(frame, p(LM.LEFT_SHOULDER),  p(LM.LEFT_ELBOW),     p(LM.LEFT_WRIST),   "L.El", live_angles[2], PURPLE)
                draw_joint(frame, p(LM.RIGHT_SHOULDER), p(LM.RIGHT_ELBOW),    p(LM.RIGHT_WRIST),  "R.El", live_angles[3], PURPLE)
                draw_joint(frame, p(LM.LEFT_HIP),       p(LM.LEFT_KNEE),      p(LM.LEFT_ANKLE),   "L.Kn", live_angles[4], ORANGE)
                draw_joint(frame, p(LM.RIGHT_HIP),      p(LM.RIGHT_KNEE),     p(LM.RIGHT_ANKLE),  "R.Kn", live_angles[5], ORANGE)

                draw_panel(frame, [
                    ("L shoulder elev", live_angles[0], GREEN),
                    ("R shoulder elev", live_angles[1], GREEN),
                    ("L elbow flex",    live_angles[2], PURPLE),
                    ("R elbow flex",    live_angles[3], PURPLE),
                    ("L knee flex",     live_angles[4], ORANGE),
                    ("R knee flex",     live_angles[5], ORANGE),
                    ("L hip flex",      live_angles[6], CYAN),
                    ("R hip flex",      live_angles[7], CYAN),
                ], h, total_reps, state_msg, prog, dev)

            else:
                cv2.putText(frame, "no person detected", (30, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, RED, 2, cv2.LINE_AA)

            cv2.imshow("Pose Tracker Engine", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
