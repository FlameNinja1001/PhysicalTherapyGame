import esper
import cv2
import time
import mediapipe as mp
from game.components.camera import CameraFrameComponent
from game.components.pose import PoseLandmarksComponent

class PoseDetectionSystem(esper.Processor):
    def __init__(self, landmarker):
        super().__init__()
        self.landmarker = landmarker
        self.start_ms = int(time.time() * 1000)

    def process(self):
        for ent, (cam, pose) in esper.get_components(CameraFrameComponent, PoseLandmarksComponent):
            if cam.frame is None:
                continue

            timestamp_ms = int(time.time() * 1000) - self.start_ms

            # Need to convert BGR to RGB for MediaPipe
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(cam.frame, cv2.COLOR_BGR2RGB)
            )

            result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                pose.landmarks = result.pose_landmarks[0]
            else:
                pose.landmarks = None
