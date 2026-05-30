import pathlib
import sys
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

def create_landmarker(model_path="pose_landmarker.task"):
    if not pathlib.Path(model_path).exists():
        print(f"ERROR: '{model_path}' not found.")
        sys.exit(1)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionTaskRunningMode.VIDEO,
        num_poses=1,
    )

    return PoseLandmarker.create_from_options(options)
