import threading
import cv2
import time
from game.core.mediapipe_manager import create_landmarker

class MediapipeThread(threading.Thread):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.running = True
        self.latest_frame = None
        self.latest_landmarks = None
        self.lock = threading.Lock()

        # Performance monitoring
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    def run(self):
        import mediapipe as mp
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

        # Explicitly use IMAGE mode for the background thread's detect() calls
        with create_landmarker(mode=VisionTaskRunningMode.IMAGE) as landmarker:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                if not self.running:
                    break

                # Flip frame here so landmarks match the mirrored display
                frame = cv2.flip(frame, 1)

                # Process MediaPipe
                try:
                    # Convert to RGB for MediaPipe
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                    # Process synchronously in this thread
                    # Ensure we haven't shut down while preparing the image
                    if self.running:
                        result = landmarker.detect(mp_image)
                    else:
                        break

                    with self.lock:
                        self.latest_frame = frame
                        if result and result.pose_landmarks:
                            self.latest_landmarks = result.pose_landmarks[0]
                        else:
                            self.latest_landmarks = None
                except Exception as e:
                    print(f"MediaPipe Thread Error: {e}")
                    if not self.running:
                        break

                self.frame_count += 1
                if time.time() - self.start_time > 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.start_time = time.time()

    def stop(self):
        self.running = False

    def get_data(self):
        with self.lock:
            return self.latest_frame, self.latest_landmarks
