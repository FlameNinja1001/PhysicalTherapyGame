"""Demo video player with zoom animations for exercise demonstrations."""
import cv2
import pygame
import os
from game.ui import theme, shapes


class DemoVideoPlayer:
    """Plays demo videos with smooth zoom animations."""

    def __init__(self, screen):
        self.screen = screen
        self.demo_cap = None
        self.current_demo_path = ""

        # Video intro state
        self.video_intro_active = False
        self.video_intro_frame_count = 0
        self.video_intro_zoom = 0.0  # 0.0 = corner, 1.0 = full screen
        self.video_intro_target_zoom = 0.0

    def get_demo_path(self, exercise_name):
        """Get the video path for an exercise template."""
        video_name = os.path.basename(exercise_name).replace('.npz', '.mov')
        path = os.path.join('training_data', 'videos', video_name)
        if os.path.exists(path):
            return path
        return ""

    def set_exercise(self, exercise_path):
        """Change the active exercise video."""
        demo_path = self.get_demo_path(exercise_path)
        if demo_path != self.current_demo_path:
            if self.demo_cap:
                self.demo_cap.release()
            self.demo_cap = cv2.VideoCapture(demo_path) if demo_path else None
            self.current_demo_path = demo_path

            # Start video intro when exercise changes
            self.video_intro_active = True
            self.video_intro_frame_count = 0
            self.video_intro_target_zoom = 1.0

    def update(self, dt):
        """Update animation state."""
        if self.video_intro_active:
            self.video_intro_frame_count += 1
            intro_duration_frames = int(4.0 / dt) if dt > 0 else 420
            if self.video_intro_frame_count > intro_duration_frames:
                self.video_intro_target_zoom = 0.0  # Zoom back to corner
                if self.video_intro_zoom < 0.1:  # Finished zooming out
                    self.video_intro_active = False

        self.video_intro_zoom += (self.video_intro_target_zoom - self.video_intro_zoom) * 5 * dt

    def draw(self):
        """Draw the demo video with zoom animation."""
        if not self.demo_cap:
            return

        # Read next frame
        ret, d_frame = self.demo_cap.read()
        if not ret:  # Loop
            self.demo_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, d_frame = self.demo_cap.read()

        if not ret:
            return

        sw, sh = self.screen.get_size()
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
        shapes.draw_parallelogram(self.screen, pygame.Rect(final_x, final_y, para_w, para_h), theme.ACCENT, 255, 5)
        self.screen.blit(d_surf, (final_x + 5, final_y + 5))

    def cleanup(self):
        """Release video capture resources."""
        if self.demo_cap:
            self.demo_cap.release()
            self.demo_cap = None
