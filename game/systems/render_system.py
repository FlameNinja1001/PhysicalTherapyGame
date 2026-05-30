import esper
import cv2
import pygame
import numpy as np
import mediapipe as mp

from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarksConnections

from game.components.camera import CameraFrameComponent
from game.components.pose import PoseLandmarksComponent, JointAnglesComponent
from game.components.exercise import ExerciseComponent, RepStateComponent
from game.components.game_state import GameStateComponent

import os

# Colours (RGB for pygame)
GREEN  = (0, 230, 120)
PURPLE = (210, 80, 240)
ORANGE = (30, 160, 255)
CYAN   = (220, 210, 60)
WHITE  = (240, 240, 240)
GRAY   = (100, 100, 110)
RED    = (220,  50, 50)

if mp.__version__ >= '0.10.30':
    from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark
    LM = PoseLandmark
else:
    LM = mp.solutions.pose.PoseLandmark

class RenderSystem(esper.Processor):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)

    def draw_joint_cv(self, frame, landmarks, idx_a, idx_b, idx_c, label, angle_deg, colour_rgb, w, h):
        def p(idx): return int(landmarks[idx].x * w), int(landmarks[idx].y * h)

        a, b, c = p(idx_a), p(idx_b), p(idx_c)
        colour_bgr = (colour_rgb[2], colour_rgb[1], colour_rgb[0])

        cv2.line(frame, a, b, colour_bgr, 2, cv2.LINE_AA)
        cv2.line(frame, b, c, colour_bgr, 2, cv2.LINE_AA)
        cv2.circle(frame, b, 7, colour_bgr, -1, cv2.LINE_AA)
        cv2.circle(frame, b, 9, (240, 240, 240), 1, cv2.LINE_AA)

        text = f"{label} {angle_deg:.0f}'"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        tx, ty = b[0] + 12, b[1] - 10
        cv2.rectangle(frame, (tx-2, ty-th-3), (tx+tw+2, ty+3), (20,10,10), -1)
        cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.48, colour_bgr, 1, cv2.LINE_AA)

    def draw_skeleton_cv(self, frame, landmarks, w, h):
        connections = PoseLandmarksConnections.POSE_LANDMARKS

        def px(lm, idx): return int(lm[idx].x * w), int(lm[idx].y * h)

        for conn in connections:
            a = px(landmarks, conn.start)
            b = px(landmarks, conn.end)
            cv2.line(frame, a, b, (75, 55, 55), 1, cv2.LINE_AA) # BGR

        for i in range(len(landmarks)):
            cv2.circle(frame, px(landmarks, i), 3, (95, 70, 70), -1, cv2.LINE_AA)

    def draw_hud(self, rep, state, ex, angles):
        # Rep Counter
        rep_text = self.font_large.render(f"REPS: {rep.rep_count} / {state.target_reps * state.level}", True, GREEN)
        self.screen.blit(rep_text, (20, 20))

        # Score & Level
        score_text = self.font_med.render(f"SCORE: {state.score}", True, CYAN)
        level_text = self.font_med.render(f"LEVEL: {state.level}", True, PURPLE)
        streak_text = self.font_small.render(f"STREAK: {state.streak}x", True, ORANGE if state.streak > 2 else WHITE)

        self.screen.blit(score_text, (20, 80))
        self.screen.blit(level_text, (20, 120))
        self.screen.blit(streak_text, (20, 160))

        # Phase / Feedback Message
        msg_color = GREEN if rep.deviation < ex.dev_thresh else RED
        if rep.state_msg == "NO TEMPLATE":
            msg_color = GRAY

        phase_text = self.font_large.render(rep.state_msg, True, msg_color)
        text_rect = phase_text.get_rect(center=(self.screen.get_width()//2, 50))
        self.screen.blit(phase_text, text_rect)

        # Progress Bar (Bottom)
        bar_w, bar_h = 400, 30
        bar_x = (self.screen.get_width() - bar_w) // 2
        bar_y = self.screen.get_height() - 50

        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(max(0, min(1.0, rep.progress)) * bar_w)
        if fill_w > 0:
            pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

        # Deviation indicator (Right side)
        dev_text = self.font_small.render(f"Form Dev: {rep.deviation:.1f}", True, msg_color)
        self.screen.blit(dev_text, (self.screen.get_width() - 200, 30))

        # Exercise Menu (Top Left)
        y = 220
        menu_title = self.font_small.render("Templates (1-9):", True, CYAN)
        self.screen.blit(menu_title, (20, y))
        y += 25
        for i, t in enumerate(state.templates):
            name = os.path.basename(t)
            prefix = "[*]" if i == state.active_idx else f"[{i+1}]"
            color = GREEN if i == state.active_idx else WHITE
            txt = self.font_small.render(f"{prefix} {name}", True, color)
            self.screen.blit(txt, (20, y))
            y += 22

    def process(self):
        for ent, (cam, pose, rep, state, ex, angles) in esper.get_components(
                CameraFrameComponent, PoseLandmarksComponent,
                RepStateComponent, GameStateComponent, ExerciseComponent, JointAnglesComponent):

            if cam.frame is None:
                continue

            # 1. Base frame processing (OpenCV)
            display_frame = cam.frame.copy()
            h, w = display_frame.shape[:2]

            # Darken background slightly
            cv2.addWeighted(display_frame, 0.6, np.zeros_like(display_frame), 0.4, 0, display_frame)

            # Draw skeleton via CV2 if pose exists
            if pose.landmarks:
                self.draw_skeleton_cv(display_frame, pose.landmarks, w, h)

                # Draw joint annotations from main.py
                self.draw_joint_cv(display_frame, pose.landmarks, LM.LEFT_HIP,       LM.LEFT_SHOULDER,  LM.LEFT_WRIST,   "L.Sh", angles.angles[0], GREEN, w, h)
                self.draw_joint_cv(display_frame, pose.landmarks, LM.RIGHT_HIP,      LM.RIGHT_SHOULDER, LM.RIGHT_WRIST,  "R.Sh", angles.angles[1], GREEN, w, h)
                self.draw_joint_cv(display_frame, pose.landmarks, LM.LEFT_SHOULDER,  LM.LEFT_ELBOW,     LM.LEFT_WRIST,   "L.El", angles.angles[2], PURPLE, w, h)
                self.draw_joint_cv(display_frame, pose.landmarks, LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW,    LM.RIGHT_WRIST,  "R.El", angles.angles[3], PURPLE, w, h)
                self.draw_joint_cv(display_frame, pose.landmarks, LM.LEFT_HIP,       LM.LEFT_KNEE,      LM.LEFT_ANKLE,   "L.Kn", angles.angles[4], ORANGE, w, h)
                self.draw_joint_cv(display_frame, pose.landmarks, LM.RIGHT_HIP,      LM.RIGHT_KNEE,     LM.RIGHT_ANKLE,  "R.Kn", angles.angles[5], ORANGE, w, h)

            # 2. Convert to Pygame Surface
            # Convert BGR to RGB for pygame
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            surface = pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), "RGB")

            # 3. Draw onto screen
            # If in fullscreen, we might want to scale the surface to fit the screen
            screen_w, screen_h = self.screen.get_size()
            if state.fullscreen:
                # Aspect ratio scaling
                img_aspect = w / h
                screen_aspect = screen_w / screen_h

                if screen_aspect > img_aspect:
                    new_h = screen_h
                    new_w = int(new_h * img_aspect)
                else:
                    new_w = screen_w
                    new_h = int(new_w / img_aspect)

                scaled_surface = pygame.transform.scale(surface, (new_w, new_h))
                # Center the surface
                self.screen.fill((0, 0, 0))
                self.screen.blit(scaled_surface, ((screen_w - new_w) // 2, (screen_h - new_h) // 2))
            else:
                self.screen.blit(surface, (0, 0))

            # 4. Draw Pygame HUD
            self.draw_hud(rep, state, ex, angles)

            # Update display
            pygame.display.flip()
