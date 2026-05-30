import esper
import cv2
import pygame
import numpy as np
import mediapipe as mp
import os
from game.components.camera import CameraFrameComponent
from game.components.pose import PoseLandmarksComponent, JointAnglesComponent
from game.components.exercise import ExerciseComponent, RepStateComponent
from game.components.game_state import GameStateComponent
from game.ui import theme, game_hud, platformer

if mp.__version__ >= '0.10.30':
    from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark
    LM = PoseLandmark
else:
    LM = mp.solutions.pose.PoseLandmark

class RenderSystem(esper.Processor):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.hud = game_hud.GameHUD(screen)
        self.minigame = platformer.PlatformerMinigame(screen, 640, 0, 640, 720)
        self.demo_cap = None
        self.current_demo_path = ""
        self.last_rep_count = 0

    def get_demo_path(self, ex_name):
        # Assumes videos are in training_data/videos/ and named similarly to .npz
        # Using .mov as found in the directory
        video_name = os.path.basename(ex_name).replace('.npz', '.mov')
        path = os.path.join('training_data', 'videos', video_name)
        if os.path.exists(path):
            return path
        return ""

    def process(self):
        dt = 1/60.0 # Approximate, could pass actual dt

        # Update logical minigame dimensions if screen resized
        sw, sh = self.screen.get_size()
        self.minigame.rect = pygame.Rect(sw // 2, 0, sw // 2, sh)

        for ent, (cam, pose, rep, state, ex, angles) in esper.get_components(
                CameraFrameComponent, PoseLandmarksComponent,
                RepStateComponent, GameStateComponent, ExerciseComponent, JointAnglesComponent):

            if cam.frame is None:
                continue

            # Reset last_rep_count if exercise changes
            if os.path.basename(ex.template_path) != os.path.basename(self.current_demo_path).replace('.mov', '.npz'):
                self.last_rep_count = 0
                self.minigame.reset_reps()

            # 1. Update Sub-systems
            self.hud.update(dt)
            self.minigame.update(dt, rep.progress, rep.rep_count)

            # Check for new rep feedback
            if rep.rep_count > self.last_rep_count:
                self.hud.set_feedback("NICE!", theme.ACCENT)
                self.last_rep_count = rep.rep_count
            elif rep.deviation > ex.dev_thresh and rep.progress > 0.1:
                # Optional: recurring feedback for poor form
                pass

            # 2. Draw Split Screen
            # Fill background
            self.screen.fill(theme.BACKGROUND)

            # --- LEFT SIDE: Webcam ---
            h, w = cam.frame.shape[:2]
            display_frame = cam.frame.copy()

            # Darken and draw skeleton
            cv2.addWeighted(display_frame, 0.6, np.zeros_like(display_frame), 0.4, 0, display_frame)
            if pose.landmarks:
                # Skeleton and joints (reuse existing logic but simpler)
                self.draw_skeleton_cv(display_frame, pose.landmarks, w, h)

            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            cam_surface = pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), "RGB")

            # Center Crop and Scale to fit left half
            target_w, target_h = sw // 2, sh

            # Calculate source rect for cropping
            src_aspect = w / h
            dst_aspect = target_w / target_h

            if src_aspect > dst_aspect:
                # Source is wider, crop sides
                src_w = int(h * dst_aspect)
                src_h = h
                src_x = (w - src_w) // 2
                src_y = 0
            else:
                # Source is taller, crop top/bottom
                src_w = w
                src_h = int(w / dst_aspect)
                src_x = 0
                src_y = (h - src_h) // 2

            cropped_surface = cam_surface.subsurface(pygame.Rect(src_x, src_y, src_w, src_h))
            scaled_cam = pygame.transform.smoothscale(cropped_surface, (target_w, target_h))
            self.screen.blit(scaled_cam, (0, 0))

            # --- RIGHT SIDE: Minigame ---
            self.minigame.draw()

            # --- CORNER: Demo Video ---
            demo_path = self.get_demo_path(ex.template_path)
            if demo_path != self.current_demo_path:
                if self.demo_cap: self.demo_cap.release()
                self.demo_cap = cv2.VideoCapture(demo_path) if demo_path else None
                self.current_demo_path = demo_path

            if self.demo_cap:
                ret, d_frame = self.demo_cap.read()
                if not ret: # Loop
                    self.demo_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, d_frame = self.demo_cap.read()

                if ret:
                    d_frame = cv2.resize(d_frame, (220, 160))
                    d_rgb = cv2.cvtColor(d_frame, cv2.COLOR_BGR2RGB)
                    d_surf = pygame.image.frombuffer(d_rgb.tobytes(), (220, 160), "RGB")

                    # Corner position (Bottom Left of the screen, over the webcam slightly or tucked in corner)
                    # Let's put it at (20, 540) so it's in the webcam's bottom left
                    self.hud.draw_parallelogram(self.screen, pygame.Rect(15, 535, 230, 170), theme.ACCENT, 255, 5)
                    self.screen.blit(d_surf, (20, 540))

            # 3. Draw HUD Overlays
            self.hud.draw(state, rep, ex)

    def draw_skeleton_cv(self, frame, landmarks, w, h):
        # Use connections from the Tasks API version
        from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarksConnections
        connections = PoseLandmarksConnections.POSE_LANDMARKS

        def px(idx): return int(landmarks[idx].x * w), int(landmarks[idx].y * h)
        for conn in connections:
            try:
                cv2.line(frame, px(conn.start), px(conn.end), (200, 200, 200), 2, cv2.LINE_AA)
            except: pass
