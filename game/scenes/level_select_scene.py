import pygame
import json
import os
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, level_card_menu, paint_effects

class LevelSelectScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.persona = persona.Persona(250, 450)
        self.persona.current_msg = "Ready to start a new mission?"

        # Load groups
        # Ensure path is correct relative to workspace root
        path = os.path.join(os.getcwd(), 'game', 'data', 'exercise_groups.json')
        with open(path, 'r') as f:
            data = json.load(f)

        self.menu = level_card_menu.LevelCardMenu(data['groups'], 550, 200)

        # Create background splatters for dramatic effect
        self.bg_splatters = [
            paint_effects.PaintSplatter(1100, 150, theme.SPLATTER_RED, size=90),
            paint_effects.PaintSplatter(200, 300, theme.SPLATTER_CYAN, size=60),
            paint_effects.PaintSplatter(900, 500, theme.SPLATTER_RED, size=50),
        ]

        # Create grunge texture
        sw, sh = screen.get_size()
        self.grunge = paint_effects.GrungeTexture(sw, sh, theme.GRAY, alpha=25)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu.prev()
            elif event.key == pygame.K_DOWN:
                self.menu.next()
            elif event.key == pygame.K_RETURN:
                self.start_level()
            elif event.key == pygame.K_ESCAPE:
                from game.scenes.main_menu_scene import MainMenuScene
                self.next_scene = MainMenuScene(self.screen)

    def start_level(self):
        group = self.menu.get_selected_group()
        from game.scenes.game_scene import GameScene
        paths = [os.path.join('training_data', e) for e in group['exercises']]
        self.next_scene = GameScene(self.screen, template_paths=paths)

    def update(self, dt):
        self.particles.update(dt)
        self.persona.update(dt)
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

        # Scale persona position based on height
        self.persona.y = sh - 270
        self.persona.draw(self.screen)

        # Draw dramatic title (Persona style)
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
        prompt_text = "↑↓ Navigate  ⏎ Confirm  Esc Back"
        prompt_surf = prompt_font.render(prompt_text, True, theme.GRAY)
        prompt_rect = prompt_surf.get_rect(bottomright=(sw - 20, sh - 20))

        bg_rect = prompt_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, theme.ACCENT_LOW, bg_rect, 1)
        self.screen.blit(prompt_surf, prompt_rect)
