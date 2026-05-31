import esper
from game.components.pose import PoseLandmarksComponent

class PoseDetectionSystem(esper.Processor):
    def __init__(self, mp_thread):
        super().__init__()
        self.mp_thread = mp_thread

    def process(self, dt=0.016):
        for ent, pose in esper.get_component(PoseLandmarksComponent):
            frame, landmarks = self.mp_thread.get_data()
            if landmarks:
                pose.landmarks = landmarks
            else:
                pose.landmarks = None
