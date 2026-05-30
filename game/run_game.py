import sys
import pygame
from game.ui import theme
from game.scenes.main_menu_scene import MainMenuScene

class SceneManager:
    def __init__(self, screen):
        self.screen = screen
        self.scene = MainMenuScene(screen)
        self.running = True
        self.fullscreen = False
        self.windowed_size = (theme.WIDTH, theme.HEIGHT)

    def toggle_fullscreen(self):
        if not self.fullscreen:
            # Store current size before going fullscreen
            self.windowed_size = self.screen.get_size()
            self.fullscreen = True
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.fullscreen = False
            # Restore previous windowed size
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

        # Update current scene screen reference
        self.scene.screen = self.screen
        self.update_subsystems()

    def update_subsystems(self):
        # Notify ECS processors if we are in GameScene
        import esper
        from game.systems.render_system import RenderSystem
        try:
            render_sys = esper.get_processor(RenderSystem)
            if render_sys:
                render_sys.screen = self.screen
        except:
            pass

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(60) / 1000.0

            # 1. Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.on_exit() # Ensure cleanup
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        self.toggle_fullscreen()

                elif event.type == pygame.VIDEORESIZE:
                    # Simplified resize to avoid tiling bugs
                    if not self.fullscreen:
                        self.screen = pygame.display.set_mode((event.w, event.h))
                        self.scene.screen = self.screen
                        self.update_subsystems()

                self.scene.handle_event(event)

            # 2. Update
            self.scene.update(dt)

            # 3. Scene switching
            if self.scene.next_scene:
                # Transition animation
                overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
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
            # Flip after all drawing is done for the current frame
            pygame.display.flip()

    def on_exit(self):
        # Global cleanup
        self.scene.on_exit()
        pygame.quit()
        sys.exit()

def main():
    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("Physio Rehab: Healthcare Hero")

    # Initialize UI Theme
    theme.init()

    # Setup Screen - Simple flags for maximum compatibility
    screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))

    # Start Manager
    manager = SceneManager(screen)
    manager.run()

    pygame.quit()

if __name__ == "__main__":
    main()
