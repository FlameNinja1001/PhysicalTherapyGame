"""Webcam view with pose skeleton overlay."""
import cv2
import pygame
import numpy as np
import mediapipe as mp

if mp.__version__ >= '0.10.30':
    from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark
    LM = PoseLandmark
else:
    LM = mp.solutions.pose.PoseLandmark


class WebcamView:
    """Handles webcam frame rendering with pose skeleton overlay."""

    def __init__(self, screen):
        self.screen = screen

    def draw_skeleton(self, frame, landmarks, w, h):
        """Draw pose skeleton on the frame using OpenCV."""
        from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarksConnections
        connections = PoseLandmarksConnections.POSE_LANDMARKS

        def px(idx):
            return int(landmarks[idx].x * w), int(landmarks[idx].y * h)

        for conn in connections:
            try:
                cv2.line(frame, px(conn.start), px(conn.end), (200, 200, 200), 2, cv2.LINE_AA)
            except:
                pass

    def draw(self, frame, landmarks=None, target_rect=None, is_locked=False):
        """
        Draw the webcam frame to screen, optionally with skeleton overlay.

        Args:
            frame: OpenCV BGR frame from camera
            landmarks: Optional pose landmarks to draw skeleton
            target_rect: Optional pygame.Rect for where to draw (defaults to left half of screen)
            is_locked: If true, darken frame and show "PLEASE WAIT"
        """
        if frame is None:
            return

        sw, sh = self.screen.get_size()

        # Calculate target area (default to left half)
        if target_rect is None:
            target_rect = pygame.Rect(0, 0, sw // 2, sh)

        h, w = frame.shape[:2]
        display_frame = frame.copy()

        # Darken frame slightly
        cv2.addWeighted(display_frame, 0.6, np.zeros_like(display_frame), 0.4, 0, display_frame)

        # Draw skeleton if landmarks provided
        if landmarks:
            self.draw_skeleton(display_frame, landmarks, w, h)

        # Convert to RGB for pygame
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        cam_surface = pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), "RGB")

        # Center crop and scale to fit target area
        target_w, target_h = target_rect.width, target_rect.height

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
        self.screen.blit(scaled_cam, (target_rect.x, target_rect.y))

        # Apply darkening and "Please Wait" if locked
        if is_locked:
            overlay = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))  # Semi-transparent black
            self.screen.blit(overlay, (target_rect.x, target_rect.y))

            import math
            from game.ui import theme
            wait_font = theme.FONTS['title']
            txt = wait_font.render("PLEASE WAIT", True, theme.WHITE)
            txt_rect = txt.get_rect(center=(target_rect.centerx, target_rect.centery - 200))

            # Subtle pulse effect
            alpha = int(155 + 100 * math.sin(pygame.time.get_ticks() * 0.005))
            txt.set_alpha(alpha)
            self.screen.blit(txt, txt_rect)
