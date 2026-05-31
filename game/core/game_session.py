"""GameSession manages the lifecycle of game hardware and ECS world."""
import cv2
import esper
import glob
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
from game.core.mediapipe_thread import MediapipeThread


class GameSession:
    """
    Manages the complete lifecycle of a game session.

    Responsibilities:
    - Camera hardware initialization
    - MediaPipe thread management
    - ECS world setup and teardown
    - System registration
    - Template loading
    """

    def __init__(self, screen, template_paths=None):
        """
        Initialize a new game session.

        Args:
            screen: Pygame screen surface
            template_paths: List of exercise template paths, or None to load all from training_data
        """
        self.screen = screen
        self.cap = None
        self.mp_thread = None
        self.player = None
        self.is_ready = False

        # Load templates
        self.templates = template_paths if template_paths else sorted(glob.glob('training_data/*.npz'))

        # Initialize hardware in background
        self._init_camera()
        self._init_ecs()
        self._init_systems()

    def _init_camera(self):
        """Initialize camera hardware and MediaPipe thread."""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.mp_thread = MediapipeThread(self.cap)
        self.mp_thread.start()

    def _init_ecs(self):
        """Initialize ECS world and create player entity."""
        esper.switch_world("game")
        esper.clear_database()  # Clean start for new game session

        # Load first exercise
        if not self.templates:
            active_ex = ExerciseComponent()
        else:
            active_ex = ExerciseLoader.load_template(self.templates[0])

        # Create player entity with all components
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

    def _init_systems(self):
        """Register all ECS systems in priority order."""
        esper.add_processor(CameraSystem(self.mp_thread), priority=60)
        esper.add_processor(PoseDetectionSystem(self.mp_thread), priority=50)
        esper.add_processor(AngleComputationSystem(), priority=40)
        esper.add_processor(RepDetectionSystem(), priority=30)
        esper.add_processor(GameLogicSystem(), priority=20)
        esper.add_processor(RenderSystem(self.screen), priority=10)

    def check_ready(self):
        """Check if camera is ready by attempting to grab a frame."""
        if not self.is_ready:
            frame, landmarks = self.mp_thread.get_data()
            if frame is not None:
                self.is_ready = True
        return self.is_ready

    def update(self, dt):
        """Update all ECS systems."""
        esper.process(dt)

    def get_state(self):
        """Get the current game state component."""
        return esper.component_for_entity(self.player, GameStateComponent)

    def get_rep_state(self):
        """Get the current rep state component."""
        return esper.component_for_entity(self.player, RepStateComponent)

    def update_screen(self, screen):
        """Update screen reference (e.g., after fullscreen toggle)."""
        self.screen = screen
        render_sys = esper.get_processor(RenderSystem)
        if render_sys:
            render_sys.screen = screen

    def cleanup(self):
        """Clean up all resources."""
        if self.mp_thread:
            self.mp_thread.stop()
            self.mp_thread.join()
        if self.cap:
            self.cap.release()
        esper.clear_database()
