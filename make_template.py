import sys
import os
import cv2
import numpy as np
import mediapipe as mp
import argparse

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
    parser = argparse.ArgumentParser(description="Create a template from video.")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("output_name", help="Name of the output template")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive GUI mode to edit keyframes")
    args = parser.parse_args()

    video_path = args.video_path
    out_name = args.output_name

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

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                sequence.append((frame_count, extract_angles(result.pose_landmarks[0])))

            frame_count += 1

    cap.release()

    if len(sequence) < 10:
        print("Error: Video too short or no poses detected.")
        return

    angles_arr = np.array([s[1] for s in sequence], dtype=np.float32)
    frame_indices = [s[0] for s in sequence]

    # --- KEYFRAME EXTRACTION LOGIC ---
    # 1. Start State: Average of the first 5 valid frames (Assuming user starts standing still)
    start_state = np.mean(angles_arr[:5], axis=0)
    auto_start_idx = frame_indices[0]

    # 2. Peak State: The frame with the maximum Euclidean distance from the Start State
    distances = np.linalg.norm(angles_arr - start_state, axis=1)
    peak_idx_in_arr = np.argmax(distances)
    peak_state = angles_arr[peak_idx_in_arr]
    auto_peak_idx = frame_indices[peak_idx_in_arr]

    # Load existing template if it exists to allow editing
    npz_path = f"{out_name}.npz"
    if os.path.exists(npz_path):
        try:
            data = np.load(npz_path)
            if 'start_idx' in data and 'peak_idx' in data:
                loaded_start = int(data['start_idx'])
                loaded_peak = int(data['peak_idx'])
                valid_frames_set = set(frame_indices)

                if loaded_start in valid_frames_set and loaded_peak in valid_frames_set:
                    auto_start_idx = loaded_start
                    auto_peak_idx = loaded_peak
                    print(f"Loaded previous keyframe indices from '{npz_path}'.")
                else:
                    print("Previous keyframes invalid for this video, reverting to auto-calculation.")
        except Exception as e:
            print(f"Could not load existing template indices: {e}")

    if args.interactive:
        print("Opening interactive GUI...")
        cv2.namedWindow('Keyframe Editor')

        cap2 = cv2.VideoCapture(video_path)
        total_frames = frame_count

        def on_trackbar(val):
            pass

        cv2.createTrackbar('Frame', 'Keyframe Editor', 0, max(0, total_frames - 1), on_trackbar)

        user_start_idx = auto_start_idx
        user_peak_idx = auto_peak_idx

        valid_frames = {s[0]: s[1] for s in sequence}

        last_trackbar_pos = -1
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        cv2.setTrackbarPos('Frame', 'Keyframe Editor', 0)

        while True:
            trackbar_pos = cv2.getTrackbarPos('Frame', 'Keyframe Editor')

            if trackbar_pos != last_trackbar_pos:
                cap2.set(cv2.CAP_PROP_POS_FRAMES, trackbar_pos)
                ret, decoded_frame = cap2.read()
                if ret:
                    frame = cv2.flip(decoded_frame, 1)
                else:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                last_trackbar_pos = trackbar_pos

            display_frame = frame.copy()
            has_pose = trackbar_pos in valid_frames

            color_pose = (0, 255, 0) if has_pose else (0, 0, 255)
            pose_text = "Pose detected" if has_pose else "No pose detected!"

            cv2.putText(display_frame, f"Frame: {trackbar_pos} / {total_frames - 1} | {pose_text}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_pose, 2)
            cv2.putText(display_frame, f"Start Frame: {user_start_idx} (press 's' to set)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0) if trackbar_pos != user_start_idx else (0, 255, 0), 2)
            cv2.putText(display_frame, f"Peak Frame: {user_peak_idx} (press 'p' to set)", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if trackbar_pos != user_peak_idx else (0, 255, 0), 2)
            cv2.putText(display_frame, "Press 'q' or ESC to save and exit", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow('Keyframe Editor', display_frame)

            key = cv2.waitKey(30) & 0xFF
            if key == ord('s'):
                if has_pose:
                    user_start_idx = trackbar_pos
                else:
                    print(f"Cannot set start frame to {trackbar_pos}: No pose detected.")
            elif key == ord('p'):
                if has_pose:
                    user_peak_idx = trackbar_pos
                else:
                    print(f"Cannot set peak frame to {trackbar_pos}: No pose detected.")
            elif key == ord('q') or key == 27:
                break

        cap2.release()
        cv2.destroyAllWindows()

        # Use single frame for start if user changed it, else average of first 5 valid frames
        if user_start_idx != auto_start_idx:
            start_state = np.array(valid_frames[user_start_idx], dtype=np.float32)
        else:
            start_state = np.mean(angles_arr[:5], axis=0)

        peak_state = np.array(valid_frames[user_peak_idx], dtype=np.float32)

        final_start_idx = user_start_idx
        final_peak_idx = user_peak_idx
    else:
        final_start_idx = auto_start_idx
        final_peak_idx = auto_peak_idx

    # Save as .npz (a zipped archive containing both keyframes)
    np.savez(f"{out_name}.npz", start=start_state, peak=peak_state, start_idx=final_start_idx, peak_idx=final_peak_idx)

    print(f"Successfully saved keyframes to '{out_name}.npz'")
    print(f"Start state frame: {final_start_idx}")
    print(f"Peak state frame: {final_peak_idx}")

if __name__ == "__main__":
    main()
