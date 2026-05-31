import pygame
import math
from game.ui import theme
from game.scenes.base_scene import BaseScene
from game.core.game_session import GameSession
from game.core.navigation import SceneNavigator
from game.ui.completion_screen import CompletionScreen

class GameScene(BaseScene):
    """Main gameplay scene - delegates to GameSession for game logic."""

    def __init__(self, screen, template_paths=None):
        super().__init__(screen)
        self.is_loading = True
        self.loading_time = 0
        self.completion_ui = None

        # Create game session (handles all hardware/ECS setup)
        self.session = GameSession(screen, template_paths)

    def handle_event(self, event):
        if self.completion_ui:
            result = self.completion_ui.handle_event(event)
            if result == "RESTART":
                self.next_scene = SceneNavigator.create_game(self.screen, self.session.templates)
            elif result == "MISSIONS":
                self.next_scene = SceneNavigator.create_level_select(self.screen)
            elif result == "MAIN MENU":
                self.next_scene = SceneNavigator.create_main_menu(self.screen)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_scene = SceneNavigator.create_main_menu(self.screen)

            # Debug hotkey: UP ARROW to simulate a rep
            elif event.key == pygame.K_UP:
                rep_state = self.session.get_rep_state()
                game_state = self.session.get_state()
                if rep_state and game_state:
                    rep_state.rep_count += 1
                    print(f"[DEBUG] Rep simulated! Count: {rep_state.rep_count}/{game_state.target_reps}")

            # Debug hotkey: C to trigger mission complete screen
            elif event.key == pygame.K_c:
                state = self.session.get_state()
                state.phase = "LEVEL_COMPLETE"
                state.score = 12345  # Set a test score
                print("[DEBUG] Mission complete triggered with hotkey 'C'")

    def update(self, dt):
        if self.is_loading:
            self.loading_time += dt
            if self.session.check_ready():
                self.is_loading = False
            return

        # Check for Level Complete
        state = self.session.get_state()

        if state.phase == "LEVEL_COMPLETE":
            if not self.completion_ui:
                self.completion_ui = CompletionScreen(self.screen, state.score)
            self.completion_ui.update(dt)
            return

        self.session.update(dt)

    def draw(self):
        if self.completion_ui:
            self.completion_ui.draw()
            return

        if self.is_loading:
            self.screen.fill(theme.BACKGROUND)
            # Persona-style loading
            from game.ui import animations
            glow = animations.oscillate(self.loading_time, 100, 2.0, 155)
            color = (0, glow, glow * 0.8)

            txt = theme.FONTS['title'].render("INITIALIZING...", True, color)
            rect = txt.get_rect(center=(theme.WIDTH//2, theme.HEIGHT//2))
            self.screen.blit(txt, rect)

            # Spinning parallelogram
            angle = self.loading_time * 5
            points = [
                (theme.WIDTH//2 - 50 + math.cos(angle)*20, theme.HEIGHT//2 + 100 + math.sin(angle)*20),
                (theme.WIDTH//2 + 50 + math.cos(angle+1)*20, theme.HEIGHT//2 + 110 + math.sin(angle+1)*20),
                (theme.WIDTH//2 + 40 + math.cos(angle+2)*20, theme.HEIGHT//2 + 130 + math.sin(angle+2)*20),
                (theme.WIDTH//2 - 60 + math.cos(angle+3)*20, theme.HEIGHT//2 + 120 + math.sin(angle+3)*20)
            ]
            pygame.draw.polygon(self.screen, theme.ACCENT, points, 3)
            return

        # RenderSystem handles the drawing to screen
        pass

    def on_exit(self):
        """Clean up game session resources."""
        if hasattr(self, 'session'):
            self.session.cleanup()
        return super().on_exit()
