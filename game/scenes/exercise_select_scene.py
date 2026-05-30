import pygame
import json
import os
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, persona_menu

class ExerciseSelectScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.persona = persona.Persona(250, 450)
        self.persona.current_msg = "Which area shall we focus on?"

        # Load groups
        with open('game/data/exercise_groups.json', 'r') as f:
            self.data = json.load(f)

        self.groups = self.data['groups']
        menu_items = [f"{g['icon']} {g['name']}" for g in self.groups] + ["BACK"]
        self.menu = persona_menu.PersonaMenu(menu_items, 600, 200)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu.prev()
            elif event.key == pygame.K_DOWN:
                self.menu.next()
            elif event.key == pygame.K_RETURN:
                self.select_option()
            elif event.key == pygame.K_ESCAPE:
                from game.scenes.main_menu_scene import MainMenuScene
                self.next_scene = MainMenuScene(self.screen)

    def select_option(self):
        idx = self.menu.selected_idx
        if idx < len(self.groups):
            # Picked a group
            from game.scenes.game_scene import GameScene
            group_exercises = self.groups[idx]['exercises']
            # We map exercise filenames to full paths
            paths = [os.path.join('training_data', e) for e in group_exercises]
            self.next_scene = GameScene(self.screen, template_paths=paths)
        else:
            # BACK
            from game.scenes.main_menu_scene import MainMenuScene
            self.next_scene = MainMenuScene(self.screen)

    def update(self, dt):
        self.particles.update(dt)
        self.persona.update(dt)
        self.menu.update(dt)

    def draw(self):
        self.screen.fill(theme.BACKGROUND)
        self.particles.draw(self.screen)
        self.persona.draw(self.screen)

        label = theme.FONTS['title'].render("EXERCISES", True, theme.ACCENT)
        self.screen.blit(label, (600, 100))

        self.menu.draw(self.screen)
