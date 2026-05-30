import pygame
import math
import random
from game.ui import theme, animations

class PlatformerMinigame:
    def __init__(self, screen, x, y, width, height):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)

        # Player state
        self.player_pos = pygame.Vector2(x + width // 2, y + height - 100)
        self.player_vel = pygame.Vector2(0, 0)
        self.is_jumping = False
        self.gravity = 800
        self.jump_force = -600

        # Camera state
        self.scroll_y = 0
        self.target_scroll_y = 0

        # World state
        self.platforms = []
        self.last_rep_count = 0

        # Generate initial vertical platforms
        for i in range(20):
            # Staggered X positions for a zigzag climb
            px = x + 150 + (i % 2) * 200 + random.randint(-50, 50)
            py = y + height - 100 - i * 180
            self.platforms.append(pygame.Rect(px, py, 150, 20))

    def update(self, dt, rep_progress, rep_count):
        # 1. Trigger Jump on Rep Completion
        if rep_count > self.last_rep_count:
            self.last_rep_count = rep_count
            self.is_jumping = True

            # Snappy physics-based jump
            idx = min(rep_count, len(self.platforms) - 1)
            target_p = self.platforms[idx]

            # Calculate required horizontal velocity to reach target in certain time
            jump_duration = 0.8
            self.player_vel.y = self.jump_force
            self.player_vel.x = (target_p.centerx - self.player_pos.x) / jump_duration

        # 2. Physics Update
        if self.is_jumping:
            self.player_vel.y += self.gravity * dt
            self.player_pos += self.player_vel * dt

            # Landing check
            idx = min(self.last_rep_count, len(self.platforms) - 1)
            target_p = self.platforms[idx]
            if self.player_vel.y > 0 and self.player_pos.y >= target_p.top - 40:
                self.player_pos.y = target_p.top - 40
                self.player_pos.x = target_p.centerx
                self.player_vel = pygame.Vector2(0, 0)
                self.is_jumping = False

                # Update camera target when landing
                self.target_scroll_y = self.player_pos.y - (self.rect.y + self.rect.height // 2)
        else:
            # While waiting for rep, stay on platform
            idx = min(self.last_rep_count, len(self.platforms) - 1)
            target_p = self.platforms[idx]
            self.player_pos.y = target_p.top - 40
            self.player_pos.x = target_p.centerx

        # 3. Camera Follow
        # Smoothly follow the player's vertical progress
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 3 * dt

    def draw(self):
        # Draw background
        bg_color = (15, 20, 30)
        pygame.draw.rect(self.screen, bg_color, self.rect)

        # Clip area for platformer
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.rect)

        # Draw platforms with vertical scroll
        for i, p in enumerate(self.platforms):
            rel_rect = p.copy()
            rel_rect.y -= self.scroll_y

            if self.rect.colliderect(rel_rect):
                # Slanted Persona style
                color = theme.ACCENT if i < self.last_rep_count else theme.ACCENT_LOW
                points = [
                    (rel_rect.x + 15, rel_rect.y),
                    (rel_rect.x + rel_rect.width + 15, rel_rect.y),
                    (rel_rect.x + rel_rect.width, rel_rect.y + rel_rect.height),
                    (rel_rect.x, rel_rect.y + rel_rect.height)
                ]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, theme.WHITE, points, 1)

        # Draw Player
        px, py = self.player_pos.x, self.player_pos.y - self.scroll_y

        # Persona character shape
        body_points = [
            (px - 15, py - 35),
            (px + 20, py - 40),
            (px + 10, py + 5),
            (px - 20, py + 10)
        ]

        # Trail effect if jumping
        if self.is_jumping:
            s = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, (0, 230, 180, 50), body_points)
            self.screen.blit(s, (0, 0))

        pygame.draw.polygon(self.screen, theme.WHITE, body_points)
        pygame.draw.polygon(self.screen, theme.ACCENT, body_points, 2)

        # Glowing eyes
        pygame.draw.circle(self.screen, theme.RED, (int(px + 5), int(py - 25)), 3)
        pygame.draw.circle(self.screen, theme.RED, (int(px + 12), int(py - 27)), 3)

        self.screen.set_clip(old_clip)
