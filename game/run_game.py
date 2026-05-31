import sys
import pygame
import esper
from game.ui import theme
from game.scenes.main_menu_scene import MainMenuScene
from game.systems.render_system import RenderSystem

TARGET_FPS = 60
MAX_DT = 0.1  # Cap dt at 100ms to prevent huge jumps during lag

class SceneManager:
    def __init__(self, screen):
        self.screen = screen
        self.scene = MainMenuScene(screen)
        self.running = True
        self.fullscreen = False
        self.windowed_size = (theme.WIDTH, theme.HEIGHT)

    def toggle_fullscreen(self):
        if not self.fullscreen:
            self.windowed_size = self.screen.get_size() # remember windowed size when unfullscreen-ing
            self.fullscreen = True
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.fullscreen = False
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

        self.scene.screen = self.screen
        self.update_subsystems()

    def update_subsystems(self):
        # Notify ECS processors if we are in GameScene
        try:
            render_sys = esper.get_processor(RenderSystem)
            if render_sys:
                render_sys.screen = self.screen
        except:
            pass

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            raw_dt = clock.tick(TARGET_FPS) / 1000.0
            dt = min(raw_dt, MAX_DT)

            # 1. Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.on_exit()
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        self.toggle_fullscreen()

                elif event.type == pygame.VIDEORESIZE:
                    if not self.fullscreen:
                        self.screen = pygame.display.set_mode((event.w, event.h))
                        self.scene.screen = self.screen
                        self.update_subsystems()

                self.scene.handle_event(event)

            # 2. Update
            self.scene.update(dt)

            # 3. Scene switching
            if self.scene.next_scene:
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

            pygame.display.flip()

    def on_exit(self):
        self.scene.on_exit()
        pygame.quit()
        sys.exit()

def main():
    pygame.init()
    theme.init()

    pygame.display.set_caption("Physio Hero: Healthcare Hero")
    screen = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT))

    manager = SceneManager(screen)
    manager.run()

    pygame.quit()

if __name__ == "__main__":
    main()
