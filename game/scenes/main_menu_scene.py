import pygame
import random
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, persona_menu, paint_effects

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.persona = persona.Persona(250, 450)

        menu_items = ["START GAME", "HOW TO PLAY", "QUIT"]
        self.menu = persona_menu.PersonaMenu(menu_items, 700, 250)

        # Create dramatic background splatters
        self.bg_splatters = [
            paint_effects.PaintSplatter(150, 120, theme.SPLATTER_RED, size=80),
            paint_effects.PaintSplatter(1000, 200, theme.SPLATTER_CYAN, size=60),
            paint_effects.PaintSplatter(400, 500, theme.SPLATTER_RED, size=50),
            paint_effects.PaintSplatter(900, 550, theme.SPLATTER_CYAN, size=70),
        ]

        # Create grunge texture
        sw, sh = screen.get_size()
        self.grunge = paint_effects.GrungeTexture(sw, sh, theme.GRAY, alpha=30)

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

        # Draw grunge texture
        self.grunge.draw(self.screen)

        # Draw background splatters
        for splatter in self.bg_splatters:
            splatter.draw(self.screen)

        self.particles.draw(self.screen)

        # Scale persona y based on current height
        self.persona.y = sh - 270
        self.persona.draw(self.screen)

        # Draw dramatic overlapping title (Persona 5 style)
        self._draw_title(sw, sh)

        self.menu.draw(self.screen)

        # Draw corner prompts (like Persona)
        self._draw_prompts()

    def _draw_title(self, sw, sh):
        """Draw dramatic overlapping title text"""
        # Large background text "PHYSIO" at angle
        title_font = pygame.font.SysFont("Arial", 120, bold=True)

        # Top large text - "PHYSIO" in red
        paint_effects.draw_slanted_text(
            self.screen, title_font, "PHYSIO",
            theme.ACCENT, (sw // 2 - 100, 100), angle=-5
        )

        # Overlapping "REHAB" in white/cyan
        rehab_font = pygame.font.SysFont("Arial", 110, bold=True)
        paint_effects.draw_slanted_text(
            self.screen, rehab_font, "REHAB",
            theme.WHITE, (sw // 2 + 50, 150), angle=-8
        )

        # Small subtitle at angle
        subtitle_font = theme.FONTS['body']
        subtitle_text = subtitle_font.render("YOUR RECOVERY JOURNEY", True, theme.CYAN)
        subtitle_rect = subtitle_text.get_rect(center=(sw // 2 + 100, 200))

        # Draw line under subtitle
        line_start = (subtitle_rect.left - 50, subtitle_rect.bottom + 5)
        line_end = (subtitle_rect.right + 30, subtitle_rect.bottom + 5)
        pygame.draw.line(self.screen, theme.ACCENT, line_start, line_end, 3)

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
