import esper
import numpy as np
import mediapipe as mp
from game.components.pose import PoseLandmarksComponent, JointAnglesComponent

if mp.__version__ >= '0.10.30':
    from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark
    LM = PoseLandmark
else:
    LM = mp.solutions.pose.PoseLandmark

def angle_at(a, b, c):
    ba = np.array(a, float) - np.array(b, float)
    bc = np.array(c, float) - np.array(b, float)
    n = np.linalg.norm(ba) * np.linalg.norm(bc)
    if n < 1e-6: return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(ba, bc) / n, -1.0, 1.0))))

class AngleComputationSystem(esper.Processor):
    def process(self, dt=0.016):
        for ent, (pose, angles) in esper.get_components(PoseLandmarksComponent, JointAnglesComponent):
            if not pose.landmarks:
                continue

            lm = pose.landmarks
            def coords(idx): return (lm[idx].x, lm[idx].y)

            # Update the 8 core joint angles
            angles.angles = [
                angle_at(coords(LM.LEFT_HIP),      coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_WRIST)),
                angle_at(coords(LM.RIGHT_HIP),     coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_WRIST)),
                angle_at(coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_ELBOW),    coords(LM.LEFT_WRIST)),
                angle_at(coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_ELBOW),   coords(LM.RIGHT_WRIST)),
                angle_at(coords(LM.LEFT_HIP),      coords(LM.LEFT_KNEE),      coords(LM.LEFT_ANKLE)),
                angle_at(coords(LM.RIGHT_HIP),     coords(LM.RIGHT_KNEE),     coords(LM.RIGHT_ANKLE)),
                angle_at(coords(LM.LEFT_SHOULDER),  coords(LM.LEFT_HIP),      coords(LM.LEFT_KNEE)),
                angle_at(coords(LM.RIGHT_SHOULDER), coords(LM.RIGHT_HIP),     coords(LM.RIGHT_KNEE))
            ]
