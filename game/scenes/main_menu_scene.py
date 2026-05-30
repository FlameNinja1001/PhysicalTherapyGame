import pygame
from game.scenes.base_scene import BaseScene
from game.ui import theme, particles, persona, persona_menu

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.particles = particles.ParticleSystem()
        self.persona = persona.Persona(250, 450)

        menu_items = ["START GAME", "HOW TO PLAY", "QUIT"]
        self.menu = persona_menu.PersonaMenu(menu_items, 600, 250)

        self.title_surf = theme.FONTS['title'].render("PHYSIO REHAB", True, theme.ACCENT)
        self.title_rect = self.title_surf.get_rect(center=(theme.WIDTH//2, 100))

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

    def draw(self):
        self.screen.fill(theme.BACKGROUND)
        self.particles.draw(self.screen)
        self.persona.draw(self.screen)

        # Title with subtle glow
        glow_rect = self.title_rect.inflate(10, 10)
        pygame.draw.rect(self.screen, theme.ACCENT_LOW, glow_rect, border_radius=15)
        self.screen.blit(self.title_surf, self.title_rect)

        self.menu.draw(self.screen)
