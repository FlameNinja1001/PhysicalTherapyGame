import pygame
import random
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, persona_menu, paint_effects, animations, hero
from game.core.navigation import SceneNavigator

class MainMenuScene(BaseScene):
    def __init__(self, screen, menu_hero=None):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()

        # Hero will be auto-positioned and scaled in update()
        # Reuse hero instance if provided, otherwise create new one
        if menu_hero is None:
            self.hero = hero.create_hero(0, 0)
            self.hero.scale = 1.0
        else:
            self.hero = menu_hero

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
            self.next_scene = SceneNavigator.create_level_select(self.screen, self.hero)
        elif choice == "QUIT":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt):
        sw, sh = self.screen.get_size()

        hero_zone_width = sw * 0.35  # Reserve 35% of screen for hero
        hero_target_height = sh * 0.65  # Hero should be 65% of screen height

        # Calculate scale to make hero fit nicely
        self.hero.scale = hero_target_height / 512  # Scale based on target height

        # Position hero in center-left zone (at bottom like standing)
        self.hero.x = hero_zone_width / 2 - 64  # Center in left zone
        self.hero.y = sh - hero_target_height - 50  # Position near bottom with padding

        # Position menu on the right side
        self.menu.x = sw * 0.55  # Start menu at 55% across screen
        self.menu.y = sh * 0.45  # Center vertically

        self.particles.update(dt)
        self.hero.update(dt)  # Update hero animation at 30 fps
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
        """Draw the animated hero character."""
        # Draw the animated hero sprite at 30 fps
        self.hero.draw(self.screen)

    def _draw_title(self, sw, sh):
        """Draw title on the right side to complement the hero on the left"""
        # Position title in the right zone (starts at 40% across screen)
        title_x = sw * 0.45
        title_y = sh * 0.12

        # "PHYSIO" in bold red with slight slant
        physio_font = pygame.font.SysFont("Arial", 85, bold=True)
        paint_effects.draw_slanted_text(
            self.screen, physio_font, "PHYSIO",
            theme.ACCENT, (title_x, title_y), angle=-3
        )

        # "HERO" in white with slight overlap and slant
        hero_font = pygame.font.SysFont("Arial", 85, bold=True)
        paint_effects.draw_slanted_text(
            self.screen, hero_font, "HERO",
            theme.WHITE, (title_x + 100, title_y + 35), angle=-4
        )

        # Clean tagline below
        subtitle_font = theme.FONTS['body']
        subtitle_text = subtitle_font.render("YOUR RECOVERY JOURNEY", True, theme.CYAN)
        subtitle_rect = subtitle_text.get_rect(left=int(title_x + 10), top=int(title_y + 95))

        # Stylish underline
        line_y = subtitle_rect.bottom + 5
        pygame.draw.line(self.screen, theme.ACCENT,
                        (subtitle_rect.left, line_y),
                        (subtitle_rect.right, line_y), 3)

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
