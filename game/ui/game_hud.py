import pygame
import math
from game.ui import theme, animations

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

    def draw_parallelogram(self, surface, rect, color, alpha=255, angle=10):
        """Draws a slanted parallelogram background."""
        width, height = rect.width, rect.height
        x, y = rect.x, rect.y
        offset = math.tan(math.radians(angle)) * height

        points = [
            (x + offset, y),
            (x + width + offset, y),
            (x + width, y + height),
            (x, y + height)
        ]

        if alpha < 255:
            s = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*color, alpha), points)
            surface.blit(s, (0, 0))
        else:
            pygame.draw.polygon(surface, color, points)

    def draw(self, state, rep, ex, total_height=0):
        sw, sh = self.screen.get_size()

        # 1. Exercise Name (Top Center Slanted Block)
        ex_name = ex.name.replace('.npz', '').replace('_', ' ').upper()
        name_txt = theme.FONTS['menu'].render(ex_name, True, theme.WHITE)
        name_w = name_txt.get_width() + 60
        bg_rect = pygame.Rect(sw // 2 - name_w // 2, 10, name_w, 50)
        self.draw_parallelogram(self.screen, bg_rect, theme.ACCENT_LOW, 220, 15)
        self.screen.blit(name_txt, (bg_rect.x + 35, bg_rect.y + 5))

        # 2. Rep Counter (Bottom Right - Persona Style Badge)
        rep_val = f"{rep.rep_count}"
        target_val = f"{state.target_reps}"

        badge_w, badge_h = 180, 120
        badge_x, badge_y = sw - badge_w - 20, sh - badge_h - 20

        badge_rect = pygame.Rect(badge_x, badge_y, badge_w, badge_h)
        self.draw_parallelogram(self.screen, badge_rect, (20, 25, 35), 255, -15)
        pygame.draw.polygon(self.screen, theme.ACCENT, [
            (badge_x + 30, badge_y), (badge_x + badge_w + 30, badge_y),
            (badge_x + badge_w, badge_y + badge_h), (badge_x, badge_y + badge_h)
        ], 3)

        rep_txt = theme.FONTS['title'].render(rep_val, True, theme.WHITE)
        slash_txt = theme.FONTS['body'].render(f"/ {target_val}", True, theme.GRAY)

        self.screen.blit(rep_txt, (badge_x + 40, badge_y + 10))
        self.screen.blit(slash_txt, (badge_x + 50, badge_y + 80))

        # 3. Progress Bar (Vertical Segments next to minigame)
        bar_x, bar_y = sw // 2 + 10, sh // 2 - 200
        bar_w, bar_h = 12, 400

        # Background segments
        num_segments = 10
        seg_w = bar_w // num_segments
        for i in range(num_segments):
            seg_rect = pygame.Rect(bar_x + i * seg_w + 2, bar_y, seg_w - 4, bar_h)
            self.draw_parallelogram(self.screen, seg_rect, (30, 35, 45), 255, 15)

            # Fill segments
            if rep.progress > (i / num_segments):
                fill_color = theme.ACCENT if rep.deviation < ex.dev_thresh else theme.RED
                self.draw_parallelogram(self.screen, seg_rect, fill_color, 255, 15)

        # 4. Score Badge (Top Right - More angled)
        score_val = f"SCORE {state.score:05d}"
        score_txt = theme.FONTS['body'].render(score_val, True, theme.BLACK)
        score_bg = pygame.Rect(sw - 260, 20, 240, 45)
        self.draw_parallelogram(self.screen, score_bg, theme.ACCENT, 255, -20)
        self.screen.blit(score_txt, (score_bg.x + 40, score_bg.y + 10))

        # 4b. Height Badge (Below Score - Cyan accent)
        if total_height > 0:
            height_val = f"HEIGHT {int(total_height)}m"
            height_txt = theme.FONTS['body'].render(height_val, True, theme.BLACK)
            height_bg = pygame.Rect(sw - 260, 75, 240, 45)
            self.draw_parallelogram(self.screen, height_bg, theme.ACCENT_SECONDARY, 255, -20)
            self.screen.blit(height_txt, (height_bg.x + 40, height_bg.y + 10))

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
