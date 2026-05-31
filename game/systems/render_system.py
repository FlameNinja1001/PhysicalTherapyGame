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

        # Video intro state
        self.video_intro_active = False
        self.video_intro_frame_count = 0
        self.video_intro_zoom = 0.0  # 0.0 = corner, 1.0 = full screen
        self.video_intro_target_zoom = 0.0

    def get_demo_path(self, ex_name):
        # Videos are in training_data/videos/
        video_name = os.path.basename(ex_name).replace('.npz', '.mov')
        path = os.path.join('training_data', 'videos', video_name)
        if os.path.exists(path):
            return path
        return ""

    def process(self):
        # minigame dimensions are based on screen size
        sw, sh = self.screen.get_size()
        self.minigame.rect = pygame.Rect(sw // 2, 0, sw // 2, sh)

        for ent, (cam, pose, rep, state, ex, angles) in esper.get_components(
                CameraFrameComponent, PoseLandmarksComponent,
                RepStateComponent, GameStateComponent, ExerciseComponent, JointAnglesComponent):

            # Get dt from state component
            dt = state.dt

            if cam.frame is None:
                continue

            # reset last_rep_count if exercise changes
            if os.path.basename(ex.template_path) != os.path.basename(self.current_demo_path).replace('.mov', '.npz'):
                self.last_rep_count = 0
                self.minigame.reset_reps()

                # Start video intro when exercise changes
                self.video_intro_active = True
                self.video_intro_frame_count = 0
                self.video_intro_target_zoom = 1.0

            # 1. Update Sub-systems
            self.hud.update(dt)
            self.minigame.update(dt, rep.progress, rep.rep_count)

            # Update video intro state
            if self.video_intro_active:
                self.video_intro_frame_count += 1
                intro_duration_frames = int(4.0 / dt) if dt > 0 else 420
                if self.video_intro_frame_count > intro_duration_frames:
                    self.video_intro_target_zoom = 0.0  # Zoom back to corner
                    if self.video_intro_zoom < 0.1:  # Finished zooming out
                        self.video_intro_active = False

            self.video_intro_zoom += (self.video_intro_target_zoom - self.video_intro_zoom) * 5 * dt

            # check for new rep feedback
            if rep.rep_count > self.last_rep_count:
                self.hud.set_feedback("NICE!", theme.ACCENT)
                self.last_rep_count = rep.rep_count
            elif rep.deviation > ex.dev_thresh and rep.progress > 0.1:
                # TODO: recurring feedback for poor form
                pass

            # 2. Draw Split Screen
            # Fill background
            self.screen.fill(theme.BACKGROUND)

            # --- LEFT SIDE: Webcam ---
            h, w = cam.frame.shape[:2]
            display_frame = cam.frame.copy()

            cv2.addWeighted(display_frame, 0.6, np.zeros_like(display_frame), 0.4, 0, display_frame)
            if pose.landmarks:
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
                    # Maintain aspect ratio
                    orig_h, orig_w = d_frame.shape[:2]
                    aspect_ratio = orig_w / orig_h

                    # Corner state: small video in bottom left
                    corner_height = 160
                    corner_width = int(corner_height * aspect_ratio)
                    corner_x = 15
                    corner_y = sh - corner_height - 25

                    # Zoomed state: fit to left half while maintaining aspect ratio, centered
                    left_half_w = sw // 2
                    left_half_h = sh

                    # Calculate zoomed dimensions maintaining aspect ratio
                    if aspect_ratio > (left_half_w / left_half_h):
                        # Video is wider, fit to width
                        zoomed_width = left_half_w
                        zoomed_height = int(left_half_w / aspect_ratio)
                    else:
                        # Video is taller, fit to height
                        zoomed_height = left_half_h
                        zoomed_width = int(left_half_h * aspect_ratio)

                    # Center the zoomed video in left half
                    zoomed_x = (left_half_w - zoomed_width) // 2
                    zoomed_y = (left_half_h - zoomed_height) // 2

                    # Lerp between corner and zoomed states
                    final_width = int(corner_width + (zoomed_width - corner_width) * self.video_intro_zoom)
                    final_height = int(corner_height + (zoomed_height - corner_height) * self.video_intro_zoom)
                    final_x = int(corner_x + (zoomed_x - corner_x) * self.video_intro_zoom)
                    final_y = int(corner_y + (zoomed_y - corner_y) * self.video_intro_zoom)

                    # Resize and convert
                    d_frame = cv2.resize(d_frame, (final_width, final_height))
                    d_rgb = cv2.cvtColor(d_frame, cv2.COLOR_BGR2RGB)
                    d_surf = pygame.image.frombuffer(d_rgb.tobytes(), (final_width, final_height), "RGB")

                    # Draw parallelogram frame
                    para_w = final_width + 10
                    para_h = final_height + 10
                    self.hud.draw_parallelogram(self.screen, pygame.Rect(final_x, final_y, para_w, para_h), theme.ACCENT, 255, 5)
                    self.screen.blit(d_surf, (final_x + 5, final_y + 5))

            # 3. Draw HUD Overlays
            self.hud.draw(state, rep, ex, self.minigame.total_height_climbed)

    def draw_skeleton_cv(self, frame, landmarks, w, h):
        from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarksConnections
        connections = PoseLandmarksConnections.POSE_LANDMARKS

        def px(idx): return int(landmarks[idx].x * w), int(landmarks[idx].y * h)
        for conn in connections:
            try:
                cv2.line(frame, px(conn.start), px(conn.end), (200, 200, 200), 2, cv2.LINE_AA)
            except: pass
