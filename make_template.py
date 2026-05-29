import sys
import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark

def angle_at(a, b, c):
    ba = np.array(a, float) - np.array(b, float)
    bc = np.array(c, float) - np.array(b, float)
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n < 1e-6: return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(ba, bc) / n, -1.0, 1.0))))

def extract_angles(lm):
    LM = PoseLandmark
    def p(idx): return (lm[idx].x, lm[idx].y) 
    
    return [
        angle_at(p(LM.LEFT_HIP),      p(LM.LEFT_SHOULDER),  p(LM.LEFT_WRIST)),
        angle_at(p(LM.RIGHT_HIP),     p(LM.RIGHT_SHOULDER), p(LM.RIGHT_WRIST)),
        angle_at(p(LM.LEFT_SHOULDER),  p(LM.LEFT_ELBOW),    p(LM.LEFT_WRIST)),
        angle_at(p(LM.RIGHT_SHOULDER), p(LM.RIGHT_ELBOW),   p(LM.RIGHT_WRIST)),
        angle_at(p(LM.LEFT_HIP),      p(LM.LEFT_KNEE),      p(LM.LEFT_ANKLE)),
        angle_at(p(LM.RIGHT_HIP),     p(LM.RIGHT_KNEE),     p(LM.RIGHT_ANKLE)),
        angle_at(p(LM.LEFT_SHOULDER),  p(LM.LEFT_HIP),      p(LM.LEFT_KNEE)),
        angle_at(p(LM.RIGHT_SHOULDER), p(LM.RIGHT_HIP),     p(LM.RIGHT_KNEE))
    ]

def main():
    if len(sys.argv) < 3:
        print("Usage: python make_template.py <path_to_video> <output_name>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    out_name = sys.argv[2]
    
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path="pose_landmarker.task"),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_poses=1,
    )
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    sequence = []
    
    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok: break
            
            frame = cv2.flip(frame, 1)
            timestamp_ms = int((frame_count / fps) * 1000)
            frame_count += 1
            
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            
            if result.pose_landmarks:
                sequence.append(extract_angles(result.pose_landmarks[0]))
                
    cap.release()
    
    if len(sequence) < 10:
        print("Error: Video too short or no poses detected.")
        return
        
    angles_arr = np.array(sequence, dtype=np.float32)
    
    # --- KEYFRAME EXTRACTION LOGIC ---
    # 1. Start State: Average of the first 5 frames (Assuming user starts standing still)
    start_state = np.mean(angles_arr[:5], axis=0)
    
    # 2. Peak State: The frame with the maximum Euclidean distance from the Start State
    distances = np.linalg.norm(angles_arr - start_state, axis=1)
    peak_idx = np.argmax(distances)
    peak_state = angles_arr[peak_idx]
    
    # Save as .npz (a zipped archive containing both keyframes)
    np.savez(f"{out_name}.npz", start=start_state, peak=peak_state)
    
    print(f"Successfully saved keyframes to '{out_name}.npz'")
    print(f"Max movement distance identified at frame {peak_idx}.")

if __name__ == "__main__":
    main()
