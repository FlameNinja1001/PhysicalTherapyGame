import esper
import cv2
from game.components.camera import CameraFrameComponent

class CameraSystem(esper.Processor):
    def __init__(self, mp_thread):
        super().__init__()
        self.mp_thread = mp_thread

    def process(self, dt=0.016):
        for ent, cam in esper.get_component(CameraFrameComponent):
            frame, landmarks = self.mp_thread.get_data()
            if frame is not None:
                # Resize if necessary or just update dimensions
                cam.height, cam.width = frame.shape[:2]
                cam.frame = frame
