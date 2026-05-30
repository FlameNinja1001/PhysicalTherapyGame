import sys
import pygame
from game.ui import theme
from game.scenes.main_menu_scene import MainMenuScene

class SceneManager:
    def __init__(self, screen):
        self.screen = screen
        self.scene = MainMenuScene(screen)
        self.running = True

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(60) / 1000.0

            # 1. Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.scene.handle_event(event)

            # 2. Update
            self.scene.update(dt)

            # 3. Scene switching
            if self.scene.next_scene:
                # Transition animation
                overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT))
                overlay.fill(theme.BLACK)

                # Fade out current scene
                for alpha in range(0, 255, 25):
                    overlay.set_alpha(alpha)
                    self.scene.draw()
                    self.screen.blit(overlay, (0, 0))
                    pygame.display.flip()
                    pygame.time.delay(5)

                self.scene.on_exit()
                self.scene = self.scene.next_scene
                self.scene.on_enter()

                # Fade in new scene while calling its update to start animations
                for alpha in range(255, 0, -25):
                    overlay.set_alpha(alpha)
                    # Force update with a fixed dt during transition to kickstart animations
                    self.scene.update(0.016)
                    self.scene.draw()
                    self.screen.blit(overlay, (0, 0))
                    pygame.display.flip()
                    pygame.time.delay(5)

            # 4. Draw
            self.scene.draw()
            pygame.display.flip()

def main():
    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("Physio Rehab: Healthcare Hero")

    # Initialize UI Theme
    theme.init()

    # Setup Screen
    screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))

    # Start Manager
    manager = SceneManager(screen)
    manager.run()

    pygame.quit()

if __name__ == "__main__":
    main()
