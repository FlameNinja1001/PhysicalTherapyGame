import sys
import glob
import cv2
import pygame
import esper

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

def main():
    # 1. Initialize Pygame
    pygame.init()
    pygame.display.set_caption("Physical Therapy Game (ECS)")
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()

    # 2. Setup Camera & MediaPipe
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("ERROR: cannot open webcam.")
        sys.exit(1)

    # 3. Load Templates
    templates = sorted(glob.glob('training_data/*.npz'))
    if not templates:
        print("No templates found in 'training_data'. Game will not track reps.")
        active_ex = ExerciseComponent()
    else:
        active_ex = ExerciseLoader.load_template(templates[0])
        print(f"Loaded template: {active_ex.name}")

    # 4. Initialize ECS World
    esper.switch_world("game")

    # Add Player Entity with all required components
    player = esper.create_entity(
        CameraFrameComponent(),
        PoseLandmarksComponent(),
        JointAnglesComponent(),
        active_ex,
        RepStateComponent(),
        GameStateComponent(
            target_reps=10,
            templates=templates,
            active_idx=0
        )
    )

    # 5. Add Systems
    with create_landmarker() as landmarker:
        esper.add_processor(CameraSystem(cap), priority=60)
        esper.add_processor(PoseDetectionSystem(landmarker), priority=50)
        esper.add_processor(AngleComputationSystem(), priority=40)
        esper.add_processor(RepDetectionSystem(), priority=30)
        esper.add_processor(GameLogicSystem(), priority=20)
        esper.add_processor(RenderSystem(screen), priority=10)

        # 6. Main Game Loop
        running = True

        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        running = False

                    if event.key == pygame.K_f:
                        state = esper.component_for_entity(player, GameStateComponent)
                        state.fullscreen = not state.fullscreen
                        if state.fullscreen:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((1280, 720))

                        # Update render system with new screen
                        render_sys = esper.get_processor(RenderSystem)
                        render_sys.screen = screen

                    # Handle numbers 1-9 to switch templates
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(templates):
                            new_ex = ExerciseLoader.load_template(templates[idx])
                            esper.add_component(player, new_ex)

                            # Reset rep state
                            esper.add_component(player, RepStateComponent())

                            state = esper.component_for_entity(player, GameStateComponent)
                            state.active_idx = idx

                            print(f"Switched to: {new_ex.name}")

            # Run ECS systems
            esper.process()

            # Cap framerate
            clock.tick(30)

    # Cleanup
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
