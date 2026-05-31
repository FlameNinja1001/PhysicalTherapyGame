import pygame
import cv2
import glob
import esper
import math

from game.ui import theme
from game.scenes.base_scene import BaseScene
from game.components.camera import CameraFrameComponent
from game.components.pose import PoseLandmarksComponent, JointAnglesComponent
from game.components.exercise import ExerciseComponent, RepStateComponent
from game.components.game_state import GameStateComponent

from game.systems.camera_system import CameraSystem
from game.systems.pose_system import PoseDetectionSystem
from game.systems.angle_system import AngleComputationSystem
from game.systems.rep_system import RepDetectionSystem
from game.systems.game_system import GameLogicSystem
from game.systems.render_system import RenderSystem

from game.core.exercise_loader import ExerciseLoader
from game.core.mediapipe_manager import create_landmarker
from game.core.mediapipe_thread import MediapipeThread
from game.ui.completion_screen import CompletionScreen

class GameScene(BaseScene):
    def __init__(self, screen, template_paths=None):
        super().__init__(screen)
        self.is_loading = True
        self.loading_time = 0
        self.completion_ui = None

        # 1. Setup Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 2. Load Templates
        self.templates = template_paths if template_paths else sorted(glob.glob('training_data/*.npz'))
        if not self.templates:
            active_ex = ExerciseComponent()
        else:
            active_ex = ExerciseLoader.load_template(self.templates[0])

        # 3. Initialize ECS World
        esper.switch_world("game")
        esper.clear_database() # Clean start for new game session

        self.player = esper.create_entity(
            CameraFrameComponent(),
            PoseLandmarksComponent(),
            JointAnglesComponent(),
            active_ex,
            RepStateComponent(),
            GameStateComponent(
                target_reps=10,
                templates=self.templates,
                active_idx=0
            )
        )

        # 4. Initialize MediaPipe Thread
        self.mp_thread = MediapipeThread(self.cap)
        self.mp_thread.start()

        # 5. Systems
        # Pass the thread to Camera and Pose systems so they can grab the latest data
        esper.add_processor(CameraSystem(self.mp_thread), priority=60)
        esper.add_processor(PoseDetectionSystem(self.mp_thread), priority=50)
        esper.add_processor(AngleComputationSystem(), priority=40)
        esper.add_processor(RepDetectionSystem(), priority=30)
        esper.add_processor(GameLogicSystem(), priority=20)
        esper.add_processor(RenderSystem(self.screen), priority=10)

    def handle_event(self, event):
        if self.completion_ui:
            result = self.completion_ui.handle_event(event)
            if result == "RESTART":
                self.next_scene = GameScene(self.screen, self.templates)
            elif result == "MISSIONS":
                from game.scenes.level_select_scene import LevelSelectScene
                self.next_scene = LevelSelectScene(self.screen)
            elif result == "MAIN MENU":
                from game.scenes.main_menu_scene import MainMenuScene
                self.next_scene = MainMenuScene(self.screen)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from game.scenes.main_menu_scene import MainMenuScene
                self.next_scene = MainMenuScene(self.screen)

            if event.key == pygame.K_f:
                state = esper.component_for_entity(self.player, GameStateComponent)
                state.fullscreen = not state.fullscreen
                if state.fullscreen:
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((1280, 720))

                render_sys = esper.get_processor(RenderSystem)
                render_sys.screen = self.screen

    def update(self, dt):
        if self.is_loading:
            self.loading_time += dt
            # Try to grab a frame from thread to see if camera is ready
            frame, landmarks = self.mp_thread.get_data()
            if frame is not None:
                # Camera is ready, stop loading
                self.is_loading = False
            return

        # Check for Level Complete
        state = esper.component_for_entity(self.player, GameStateComponent)

        # Store dt in state component so systems can access it
        state.dt = dt

        if state.phase == "LEVEL_COMPLETE":
            if not self.completion_ui:
                self.completion_ui = CompletionScreen(self.screen, state.score)
            self.completion_ui.update(dt)
            return

        esper.process()

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
        # Cleanup
        if hasattr(self, 'mp_thread'):
            self.mp_thread.stop()
            self.mp_thread.join()
        if hasattr(self, 'cap'):
            self.cap.release()
        esper.clear_database()
        return super().on_exit()
