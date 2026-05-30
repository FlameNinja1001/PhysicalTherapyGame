import pygame
import math
from game.ui import theme, animations

class Persona:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.base_y = y
        self.wave_angle = 0
        self.blink_timer = 0
        self.is_blinking = False
        self.msg_timer = 0
        self.current_msg = "Ready for today's exercises?"

    def update(self, dt):
        # Bounce animation
        self.y = self.base_y + animations.oscillate(pygame.time.get_ticks() * 0.001, 10, 0.5)

        # Wave animation for arms
        self.wave_angle = animations.oscillate(pygame.time.get_ticks() * 0.001, 0.2, 1.0)

        # Blinking
        self.blink_timer += dt
        if self.blink_timer > 3.0:
            self.is_blinking = True
            if self.blink_timer > 3.15:
                self.is_blinking = False
                self.blink_timer = 0

    def draw(self, surface):
        # 1. Body
        body_rect = pygame.Rect(self.x - 40, self.y + 60, 80, 100)
        pygame.draw.ellipse(surface, theme.WHITE, body_rect)
        pygame.draw.ellipse(surface, theme.ACCENT, body_rect, 3)

        # 2. Head
        head_center = (self.x, self.y + 20)
        pygame.draw.circle(surface, theme.WHITE, head_center, 35)
        pygame.draw.circle(surface, theme.ACCENT, head_center, 35, 3)

        # 3. Eyes
        eye_y = self.y + 15
        if self.is_blinking:
            pygame.draw.line(surface, theme.BLACK, (self.x - 15, eye_y), (self.x - 5, eye_y), 2)
            pygame.draw.line(surface, theme.BLACK, (self.x + 5, eye_y), (self.x + 15, eye_y), 2)
        else:
            pygame.draw.circle(surface, theme.BLACK, (self.x - 10, eye_y), 4)
            pygame.draw.circle(surface, theme.BLACK, (self.x + 10, eye_y), 4)

        # 4. Arms (Waving)
        # Left arm
        l_arm_start = (self.x - 30, self.y + 70)
        l_arm_end = (self.x - 70, self.y + 40 + math.sin(self.wave_angle) * 20)
        pygame.draw.line(surface, theme.WHITE, l_arm_start, l_arm_end, 12)
        pygame.draw.line(surface, theme.ACCENT, l_arm_start, l_arm_end, 3)

        # Right arm (Holding clipboard)
        r_arm_start = (self.x + 30, self.y + 70)
        r_arm_end = (self.x + 60, self.y + 80)
        pygame.draw.line(surface, theme.WHITE, r_arm_start, r_arm_end, 12)

        # Clipboard
        clip_rect = pygame.Rect(r_arm_end[0] - 10, r_arm_end[1] - 20, 30, 40)
        pygame.draw.rect(surface, (200, 200, 200), clip_rect)
        pygame.draw.rect(surface, theme.BLACK, clip_rect, 2)

        # 5. Speech Bubble
        bubble_x, bubble_y = self.x + 80, self.y - 40
        msg_surf = theme.FONTS['small'].render(self.current_msg, True, theme.BLACK)
        bw, bh = msg_surf.get_width() + 20, msg_surf.get_height() + 20

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bw, bh)
        pygame.draw.rect(surface, theme.WHITE, bubble_rect, border_radius=10)
        pygame.draw.polygon(surface, theme.WHITE, [(bubble_x, bubble_y+20), (bubble_x-15, bubble_y+10), (bubble_x, bubble_y+5)])
        surface.blit(msg_surf, (bubble_x + 10, bubble_y + 10))
