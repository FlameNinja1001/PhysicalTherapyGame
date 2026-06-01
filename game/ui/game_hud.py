import pygame
import math
from game.ui import theme, animations, shapes

class GameHUD:
    def __init__(self, screen):
        self.screen = screen
        self.particles = [] # Special HUD particles
        self.shake_amount = 0
        self.feedback_msg = ""
        self.feedback_timer = 0
        self.feedback_color = theme.ACCENT

    def set_feedback(self, msg, color=theme.ACCENT):
        self.feedback_msg = msg
        self.feedback_timer = 1.5
        self.feedback_color = color
        self.shake_amount = 10

    def update(self, dt):
        if self.shake_amount > 0:
            self.shake_amount = max(0, self.shake_amount - 40 * dt)

        if self.feedback_timer > 0:
            self.feedback_timer -= dt

    def draw(self, state, rep, ex, total_height=0, minigame_type="platformer"):
        sw, sh = self.screen.get_size()

        # 1. Exercise Name (Top Center Slanted Block)
        ex_name = ex.name.replace('.npz', '').replace('_', ' ').upper()
        name_txt = theme.FONTS['menu'].render(ex_name, True, theme.WHITE)
        name_w = name_txt.get_width() + 60
        bg_rect = pygame.Rect(sw // 2 - name_w // 2, 10, name_w, 50)
        shapes.draw_parallelogram(self.screen, bg_rect, theme.ACCENT_LOW, 220, 15)
        self.screen.blit(name_txt, (bg_rect.x + 35, bg_rect.y + 5))

        # 2. Rep Counter (Bottom Right - Persona Style Badge)
        rep_val = f"{rep.rep_count}"
        target_val = f"{state.target_reps}"

        badge_w, badge_h = 180, 120
        badge_x, badge_y = sw - badge_w - 20, sh - badge_h - 20

        badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
        shapes.draw_parallelogram(self.screen, badge_rect, (20, 25, 35), 255, -15)

        # Draw outline matching the parallelogram slant (-15 degrees)
        slant = -15
        pygame.draw.polygon(self.screen, theme.ACCENT, [
            (badge_x + slant, badge_y),
            (badge_x + badge_w + slant, badge_y),
            (badge_x + badge_w, badge_y + badge_h),
            (badge_x, badge_y + badge_h)
        ], 3)

        rep_txt = theme.FONTS['title'].render(rep_val, True, theme.WHITE)
        slash_txt = theme.FONTS['body'].render(f"/ {target_val}", True, theme.GRAY)

        self.screen.blit(rep_txt, (badge_x + 40, badge_y + 10))
        self.screen.blit(slash_txt, (badge_x + 50, badge_y + 80))

        # 4b. Progress Badge (Below Score - Cyan accent) - Dynamic label and width
        if total_height > 0:
            # Choose label based on minigame type
            if minigame_type == "platformer":
                progress_label = "HEIGHT"
            else:
                progress_label = "DISTANCE"

            progress_val = f"{progress_label} {int(total_height)}m"
            progress_txt = theme.FONTS['body'].render(progress_val, True, theme.BLACK)
            progress_w = progress_txt.get_width() + 80  # Add padding
            progress_bg = pygame.Rect(sw - progress_w - 20, 20, progress_w, 45)
            shapes.draw_parallelogram(self.screen, progress_bg, theme.ACCENT_SECONDARY, 255, -20)
            self.screen.blit(progress_txt, (progress_bg.x + 40, progress_bg.y + 10))

        # 5. Feedback Messages (Slam in effect)
        if self.feedback_timer > 0:
            alpha = int(min(1.0, self.feedback_timer * 2) * 255)
            msg_txt = theme.FONTS['title'].render(self.feedback_msg, True, self.feedback_color)

            # Add "3D" shadow
            shadow_txt = theme.FONTS['title'].render(self.feedback_msg, True, (20, 20, 20))

            # Offset based on shake
            ox = random.randint(-int(self.shake_amount), int(self.shake_amount)) if self.shake_amount > 0 else 0
            oy = random.randint(-int(self.shake_amount), int(self.shake_amount)) if self.shake_amount > 0 else 0

            center_x = theme.WIDTH // 2 + ox
            center_y = theme.HEIGHT // 2 + oy

            msg_rect = msg_txt.get_rect(center=(center_x, center_y))

            # Scaling effect
            scale = 1.0 + (self.feedback_timer > 1.3) * (self.feedback_timer - 1.3) * 5
            if scale > 1.0:
                msg_txt = pygame.transform.rotozoom(msg_txt, 0, scale)
                shadow_txt = pygame.transform.rotozoom(shadow_txt, 0, scale)
                msg_rect = msg_txt.get_rect(center=(center_x, center_y))

            shadow_txt.set_alpha(alpha)
            msg_txt.set_alpha(alpha)

            self.screen.blit(shadow_txt, (msg_rect.x + 5, msg_rect.y + 5))
            self.screen.blit(msg_txt, msg_rect)

import random
