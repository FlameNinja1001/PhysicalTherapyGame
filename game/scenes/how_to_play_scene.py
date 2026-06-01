import pygame
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, paint_effects, hero
from game.core.navigation import SceneNavigator
from game.core.audio_manager import get_audio_manager

class HowToPlayScene(BaseScene):
    def __init__(self, screen, menu_hero=None):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()

        if menu_hero is None:
            self.hero = hero.create_hero(0, 0)
        else:
            self.hero = menu_hero

        self.audio = get_audio_manager()

        sw, sh = screen.get_size()
        self.grunge = paint_effects.GrungeTexture(sw, sh, theme.GRAY, alpha=20)

        # Load how to play logo/title if available
        try:
            logo_orig = pygame.image.load('game/data/how_to_play.png').convert_alpha()
            target_w = 700
            ratio = target_w / logo_orig.get_width()
            target_h = int(logo_orig.get_height() * ratio)
            self.logo = pygame.transform.smoothscale(logo_orig, (target_w, target_h))
        except:
            self.logo = None

        self.instructions = [
            "• Navigate menus with the Up and Down arrow keys!",
            "• Press 'Enter' to choose a menu option!",
            "• When in a mission, mimic the exercise on screen to move the player.",
            "• Complete all reps of an exercise to move to the next one.",
            "• Press 'Esc' at any time to return to the main menu."
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self.audio.play_sfx('choose')
                self.next_scene = SceneNavigator.create_main_menu(self.screen, self.hero)

    def update(self, dt):
        sw, sh = self.screen.get_size()

        hero_zone_width = sw * 0.55  # Reserve 35% of screen for hero
        hero_target_height = sh * 0.85  # Hero should be 65% of screen height
        self.hero.scale = hero_target_height / 512
        self.hero.x = hero_zone_width / 2 - 384
        self.hero.y = sh - hero_target_height

        self.particles.update(dt)
        self.hero.update(dt)

    def draw(self):
        sw, sh = self.screen.get_size()
        self.screen.fill(theme.BACKGROUND)

        self.grunge.draw(self.screen)
        self.particles.draw(self.screen)
        self.hero.draw(self.screen)

        # Draw Title
        if self.logo:
            title_x = int(sw * 0.4)
            self.screen.blit(self.logo, (title_x, 50))
        else:
            title_x = int(sw * 0.4)
            title_font = pygame.font.SysFont("Arial", 80, bold=True)
            paint_effects.draw_slanted_text(self.screen, title_font, "HOW TO PLAY",
                                          theme.ACCENT, (title_x + 200, 100), angle=-3)

        # Draw Instructions with Word Wrap
        content_x = int(sw * 0.4)
        content_y = 220
        max_width = int(sw * 0.55)  # Leave margin on right

        font = theme.FONTS['body']
        current_y = content_y

        for text in self.instructions:
            # Word wrap logic
            words = text.split(' ')
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                w, h = font.size(test_line)

                if w > max_width:
                    # Render current line and start new one
                    line_surf = font.render(' '.join(current_line), True, theme.WHITE)
                    self.screen.blit(line_surf, (content_x, current_y))
                    current_y += h + 5
                    current_line = [word]
                else:
                    current_line.append(word)

            # Render remaining line
            if current_line:
                line_surf = font.render(' '.join(current_line), True, theme.WHITE)
                self.screen.blit(line_surf, (content_x, current_y))
                current_y += font.get_linesize() + 15 # Extra spacing between bullet points

        # Draw back prompt
        prompt_font = theme.FONTS['small']
        prompt_surf = prompt_font.render("Press ESC or ENTER to go back", True, theme.GRAY)
        prompt_rect = prompt_surf.get_rect(bottomright=(sw - 20, sh - 20))
        self.screen.blit(prompt_surf, prompt_rect)
