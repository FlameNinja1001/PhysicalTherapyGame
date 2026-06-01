import pygame
import json
import os
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, hero, level_card_menu, paint_effects
from game.core.navigation import SceneNavigator
from game.core.audio_manager import get_audio_manager

class LevelSelectScene(BaseScene):
    def __init__(self, screen, menu_hero=None):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.logo = None

        # Hero will be auto-positioned and scaled in update()
        # Reuse hero instance if provided, otherwise create new one
        if menu_hero is None:
            self.hero = hero.create_hero(0, 0)
            self.hero.scale = 1.0
        else:
            self.hero = menu_hero

        # Load groups
        # Ensure path is correct relative to workspace root
        path = os.path.join(os.getcwd(), 'game', 'data', 'exercise_groups.json')
        with open(path, 'r') as f:
            data = json.load(f)

        self.menu = level_card_menu.LevelCardMenu(data['groups'], 550, 200)

        # Create background splatters for dramatic effect
        self.bg_splatters = [
            paint_effects.PaintSplatter(100, 100, theme.SPLATTER_RED, size=90),
            paint_effects.PaintSplatter(200, 600, theme.SPLATTER_CYAN, size=60),
            paint_effects.PaintSplatter(1100, 650, theme.SPLATTER_RED, size=50),
        ]

        # Create grunge texture
        sw, sh = screen.get_size()
        self.grunge = paint_effects.GrungeTexture(sw, sh, theme.GRAY, alpha=25)

        # Audio manager
        self.audio = get_audio_manager()

        # Load logo
        try:
            logo_orig = pygame.image.load('game/data/mission_select.png').convert_alpha()
            target_w = 700
            ratio = target_w / logo_orig.get_width()
            target_h = int(logo_orig.get_height() * ratio)
            self.logo = pygame.transform.smoothscale(logo_orig, (target_w, target_h))
        except:
            self.logo = None
            print("Warning: Could not load game/data/mission_select.png")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu.prev()
                self.audio.play_sfx('select')
            elif event.key == pygame.K_DOWN:
                self.menu.next()
                self.audio.play_sfx('select')
            elif event.key == pygame.K_RETURN:
                self.start_level()
            elif event.key == pygame.K_ESCAPE:
                self.audio.play_sfx('choose')
                self.next_scene = SceneNavigator.create_main_menu(self.screen, self.hero)

    def start_level(self):
        self.audio.play_sfx('choose')
        self.audio.play_sfx('start_mission')
        group = self.menu.get_selected_group()
        paths = [os.path.join('training_data', e) for e in group['exercises']]
        self.next_scene = SceneNavigator.create_game(self.screen, template_paths=paths)

    def on_enter(self):
        """Called when entering this scene."""
        # Play mission select voice
        self.audio.play_voice('mission_select')

    def on_exit(self):
        """Called when leaving this scene."""
        pass

    def update(self, dt):
        sw, sh = self.screen.get_size()

        hero_zone_width = sw * 0.55  # Reserve 35% of screen for hero
        hero_target_height = sh * 0.85  # Hero should be 65% of screen height

        # Calculate scale to make hero fit nicely
        self.hero.scale = hero_target_height / 512  # Scale based on target height

        # Position hero in center-left zone (at bottom like standing)
        self.hero.x = hero_zone_width / 2 - 384  # Center in left zone
        self.hero.y = sh - hero_target_height # Position near bottom with padding

        self.particles.update(dt)
        self.hero.update(dt)  # Update hero animation at 30 fps
        self.menu.update(dt)

    def draw(self):
        sw, sh = self.screen.get_size()
        self.screen.fill(theme.BACKGROUND)

        # Draw grunge texture first
        self.grunge.draw(self.screen)

        # Draw background splatters for dramatic effect
        for splatter in self.bg_splatters:
            splatter.draw(self.screen)

        self.particles.draw(self.screen)

        # Draw the animated hero character
        self.hero.draw(self.screen)

        # Draw dramatic title (Persona style)
        if self.logo:
            # Draw logo image
            self.screen.blit(self.logo, (450, 60))
        else:
            title_font = pygame.font.SysFont("Arial", 110, bold=True)
            paint_effects.draw_slanted_text(
                self.screen, title_font, "MISSION",
                theme.ACCENT, (700, 100), angle=-6
            )

            # Subtitle
            subtitle_font = pygame.font.SysFont("Arial", 80, bold=True)
            paint_effects.draw_slanted_text(
                self.screen, subtitle_font, "SELECT",
                theme.WHITE, (850, 140), angle=-8
            )

        self.menu.draw(self.screen)

        # Draw navigation prompts
        prompt_font = theme.FONTS['small']
        prompt_text = "ARROWS Navigate  ENTER Confirm  ESC Back"
        prompt_surf = prompt_font.render(prompt_text, True, theme.GRAY)
        prompt_rect = prompt_surf.get_rect(bottomright=(sw - 20, sh - 20))

        bg_rect = prompt_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, theme.ACCENT_LOW, bg_rect, 1)
        self.screen.blit(prompt_surf, prompt_rect)
