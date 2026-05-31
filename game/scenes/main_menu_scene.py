import pygame
import random
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, persona_menu, paint_effects, animations

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.persona = persona.Persona(250, 450)

        menu_items = ["START GAME", "HOW TO PLAY", "QUIT"]
        self.menu = persona_menu.PersonaMenu(menu_items, 800, 320)

        self.bg_splatters = [
            paint_effects.PaintSplatter(120, 150, theme.SPLATTER_RED, size=60),
        ]

        sw, sh = screen.get_size()
        self.grunge = paint_effects.GrungeTexture(sw, sh, theme.GRAY, alpha=15)

        # Animation timer for effects
        self.anim_time = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu.prev()
            elif event.key == pygame.K_DOWN:
                self.menu.next()
            elif event.key == pygame.K_RETURN:
                self.select_option()

    def select_option(self):
        choice = self.menu.items[self.menu.selected_idx]
        if choice == "START GAME":
            from game.scenes.level_select_scene import LevelSelectScene
            self.next_scene = LevelSelectScene(self.screen)
        elif choice == "QUIT":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        self.particles.update(dt)
        self.persona.update(dt)
        self.menu.update(dt)
        self.anim_time += dt

    def draw(self):
        sw, sh = self.screen.get_size()
        self.screen.fill(theme.BACKGROUND)

        self.particles.draw(self.screen)
        self._draw_character(sw, sh)
        self._draw_title(sw, sh)

        self.menu.draw(self.screen)

        self._draw_prompts()

    def _draw_character(self, sw, sh):
        """Draw a large stylized character on the left side"""

        # Large circle for head
        head_y = sh // 2 + int(animations.oscillate(self.anim_time, 15, 1.5))
        head_center = (200, head_y)
        pygame.draw.circle(self.screen, theme.ACCENT, head_center, 80)
        pygame.draw.circle(self.screen, theme.WHITE, head_center, 80, 5)

        # Eyes
        eye_y = head_y - 10
        pygame.draw.circle(self.screen, theme.WHITE, (180, eye_y), 12)
        pygame.draw.circle(self.screen, theme.WHITE, (220, eye_y), 12)

        # Stylish angular body
        body_points = [
            (200, head_y + 80),
            (240, head_y + 120),
            (230, head_y + 200),
            (200, head_y + 220),
            (170, head_y + 200),
            (160, head_y + 120)
        ]
        pygame.draw.polygon(self.screen, theme.ACCENT, body_points)
        pygame.draw.polygon(self.screen, theme.WHITE, body_points, 5)

        # Arms - angular style
        # Left arm
        arm_wave = int(animations.oscillate(self.anim_time, 20, 2.0))
        left_arm = [(160, head_y + 120), (120, head_y + 150 + arm_wave), (130, head_y + 160 + arm_wave)]
        pygame.draw.polygon(self.screen, theme.CYAN, left_arm)

        # Right arm
        right_arm = [(240, head_y + 120), (280, head_y + 150 - arm_wave), (270, head_y + 160 - arm_wave)]
        pygame.draw.polygon(self.screen, theme.CYAN, right_arm)

    def _draw_title(self, sw, sh):
        """Draw title with subtle overlap (Persona style)"""
        # "PHYSIO" in bold red with slight slant
        physio_font = pygame.font.SysFont("Arial", 100, bold=True)
        paint_effects.draw_slanted_text(
            self.screen, physio_font, "PHYSIO",
            theme.ACCENT, (sw // 2 - 40, 100), angle=-3
        )

        # "REHAB" in white with slight overlap and slant
        rehab_font = pygame.font.SysFont("Arial", 100, bold=True)
        paint_effects.draw_slanted_text(
            self.screen, rehab_font, "REHAB",
            theme.WHITE, (sw // 2 + 60, 130), angle=-4
        )

        # Clean tagline below
        subtitle_font = theme.FONTS['body']
        subtitle_text = subtitle_font.render("YOUR RECOVERY JOURNEY", True, theme.CYAN)
        subtitle_rect = subtitle_text.get_rect(center=(sw // 2, 210))

        # Stylish underline
        line_y = subtitle_rect.bottom + 5
        pygame.draw.line(self.screen, theme.ACCENT,
                        (subtitle_rect.left - 50, line_y),
                        (subtitle_rect.right + 50, line_y), 3)

        self.screen.blit(subtitle_text, subtitle_rect)

    def _draw_prompts(self):
        """Draw UI prompts in corners (Persona style)"""
        sw, sh = self.screen.get_size()

        # Bottom right prompt
        prompt_font = theme.FONTS['small']
        prompt_text = "↑↓ Navigate  ⏎ Confirm"
        prompt_surf = prompt_font.render(prompt_text, True, theme.GRAY)
        prompt_rect = prompt_surf.get_rect(bottomright=(sw - 20, sh - 20))

        # Draw subtle background
        bg_rect = prompt_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), bg_rect)
        pygame.draw.rect(self.screen, theme.ACCENT_LOW, bg_rect, 1)

        self.screen.blit(prompt_surf, prompt_rect)
