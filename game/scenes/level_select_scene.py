import pygame
import json
import os
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, level_card_menu

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

        self.menu = level_card_menu.LevelCardMenu(data['groups'], 500, 180)

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
        self.screen.fill(theme.BACKGROUND)
        self.particles.draw(self.screen)
        self.persona.draw(self.screen)

        title = theme.FONTS['title'].render("MISSION SELECT", True, theme.ACCENT)
        self.screen.blit(title, (500, 80))

        self.menu.draw(self.screen)
