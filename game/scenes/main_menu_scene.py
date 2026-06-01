import pygame
import random
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona_menu, paint_effects, animations, hero
from game.core.navigation import SceneNavigator
from game.core.audio_manager import get_audio_manager

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

        # Audio manager
        self.audio = get_audio_manager()

        # Load logo
        try:
            logo_orig = pygame.image.load('game/data/logo.png').convert_alpha()
            # Scale logo to a reasonable width (e.g., 400px) while maintaining aspect ratio
            target_w = 700
            ratio = target_w / logo_orig.get_width()
            target_h = int(logo_orig.get_height() * ratio)
            self.logo = pygame.transform.smoothscale(logo_orig, (target_w, target_h))
        except:
            self.logo = None
            print("Warning: Could not load game/data/logo.png")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Debug: Individual Audio Clip Testing
            if event.key == pygame.K_1: self.audio.play_sfx("choose")
            elif event.key == pygame.K_2: self.audio.play_sfx("select")
            elif event.key == pygame.K_3: self.audio.play_sfx("start_mission")
            elif event.key == pygame.K_4: self.audio.play_sfx("video_popup")
            elif event.key == pygame.K_5: self.audio.play_sfx("mission_complete")
            elif event.key == pygame.K_6: self.audio.play_sfx("rep")
            elif event.key == pygame.K_q: self.audio.play_voice("welcome")
            elif event.key == pygame.K_w: self.audio.play_voice("mission_select")
            elif event.key == pygame.K_e: self.audio.play_voice("complete")
            elif event.key == pygame.K_a: self.audio.play_music("title")
            elif event.key == pygame.K_s: self.audio.play_music("cloud")
            elif event.key == pygame.K_d: self.audio.play_music("jungle")
            elif event.key == pygame.K_f: self.audio.play_music("water")
            elif event.key == pygame.K_g: self.audio.play_music("victory")
            elif event.key == pygame.K_SPACE: self.audio.stop_music()

            if event.key == pygame.K_UP:
                self.menu.prev()
                self.audio.play_sfx('select')
            elif event.key == pygame.K_DOWN:
                self.menu.next()
                self.audio.play_sfx('select')
            elif event.key == pygame.K_RETURN:
                self.select_option()

    def select_option(self):
        self.audio.play_sfx('choose')
        choice = self.menu.items[self.menu.selected_idx]
        if choice == "START GAME":
            self.next_scene = SceneNavigator.create_level_select(self.screen, self.hero)
        elif choice == "HOW TO PLAY":
            self.next_scene = SceneNavigator.create_how_to_play(self.screen, self.hero)
        elif choice == "QUIT":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def on_enter(self):
        """Called when entering this scene."""
        # Play title music and welcome voice
        self.audio.play_music('title')
        self.audio.play_voice('welcome')

    def on_exit(self):
        """Called when leaving this scene."""
        # Music will continue or be changed by next scene
        pass

    def update(self, dt):
        sw, sh = self.screen.get_size()

        hero_zone_width = sw * 0.55  # Reserve 35% of screen for hero
        hero_target_height = sh * 0.85 # Hero should be 65% of screen height

        # Calculate scale to make hero fit nicely
        self.hero.scale = hero_target_height / 512  # Scale based on target height

        # Position hero in center-left zone (at bottom like standing)
        self.hero.x = hero_zone_width / 2 - 384  # Center in left zone
        self.hero.y = sh - hero_target_height  # Position near bottom with padding

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
        """Draw title logo on the right side to complement the hero on the left"""
        # Position logo in the right zone (starts at 45% across screen)
        title_x = sw * 0.40
        title_y = sh * 0.05

        if self.logo:
            # Draw logo image
            self.screen.blit(self.logo, (title_x, title_y))

            # Reposition tagline below the logo
            logo_bottom = title_y + self.logo.get_height()
            subtitle_font = theme.FONTS['body']
            subtitle_text = subtitle_font.render("YOUR RECOVERY JOURNEY", True, theme.WHITE)
            subtitle_rect = subtitle_text.get_rect(left=int(title_x + 150), top=int(logo_bottom + 10))

            # Stylish underline
            line_y = subtitle_rect.bottom + 5
            pygame.draw.line(self.screen, theme.ACCENT,
                            (subtitle_rect.left, line_y),
                            (subtitle_rect.right, line_y), 3)

            self.screen.blit(subtitle_text, subtitle_rect)
        else:
            # Fallback to text if logo missing
            physio_font = pygame.font.SysFont("Arial", 85, bold=True)
            paint_effects.draw_slanted_text(
                self.screen, physio_font, "PHYSIO",
                theme.ACCENT, (title_x, title_y), angle=-3
            )

            hero_font = pygame.font.SysFont("Arial", 85, bold=True)
            paint_effects.draw_slanted_text(
                self.screen, hero_font, "HERO",
                theme.WHITE, (title_x + 100, title_y + 35), angle=-4
            )

            subtitle_font = theme.FONTS['body']
            subtitle_text = subtitle_font.render("YOUR RECOVERY JOURNEY", True, theme.CYAN)
            subtitle_rect = subtitle_text.get_rect(left=int(title_x + 10), top=int(title_y + 95))

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
        prompt_text = "ARROWS Navigate  ENTER Confirm"
        prompt_surf = prompt_font.render(prompt_text, True, theme.GRAY)
        prompt_rect = prompt_surf.get_rect(bottomright=(sw - 20, sh - 20))

        # Draw subtle background
        bg_rect = prompt_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), bg_rect)
        pygame.draw.rect(self.screen, theme.ACCENT_LOW, bg_rect, 1)

        self.screen.blit(prompt_surf, prompt_rect)
