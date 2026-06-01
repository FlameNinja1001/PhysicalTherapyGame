import pathlib
import sys
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
from game.core.paths import resource_path

def create_landmarker(model_path="pose_landmarker.task", mode=VisionTaskRunningMode.VIDEO):
    # Resolve the model path using resource_path for PyInstaller compatibility
    resolved_path = resource_path(model_path)
    
    if not pathlib.Path(resolved_path).exists():
        print(f"ERROR: '{resolved_path}' not found.")
        sys.exit(1)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=resolved_path),
        running_mode=mode,
        num_poses=1,
    )

    return PoseLandmarker.create_from_options(options)
