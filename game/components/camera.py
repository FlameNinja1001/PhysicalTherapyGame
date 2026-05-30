from dataclasses import dataclass
import numpy as np

@dataclass
class CameraFrameComponent:
    frame: np.ndarray | None = None
    width: int = 1280
    height: int = 720
