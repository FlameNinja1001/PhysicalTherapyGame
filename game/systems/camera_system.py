import esper
import cv2
from game.components.camera import CameraFrameComponent

class CameraSystem(esper.Processor):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap

    def process(self):
        for ent, cam in esper.get_component(CameraFrameComponent):
            ok, frame = self.cap.read()
            if ok:
                # Mirror so it feels like a mirror
                frame = cv2.flip(frame, 1)

                # Resize if necessary or just update dimensions
                cam.height, cam.width = frame.shape[:2]
                cam.frame = frame
