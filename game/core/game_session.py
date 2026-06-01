"""GameSession manages the lifecycle of game hardware and ECS world."""
import cv2
import esper
import glob
from game.core.paths import resource_path
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

    def __init__(self, screen, template_paths=None, audio_manager=None):
        """
        Initialize a new game session.

        Args:
            screen: Pygame screen surface
            template_paths: List of exercise template paths, or None to load all from training_data
            audio_manager: AudioManager instance for playing sounds and music
        """
        self.screen = screen
        self.cap = None
        self.mp_thread = None
        self.player = None
        self.is_ready = False
        self.audio = audio_manager

        # Load templates
        self.templates = template_paths if template_paths else sorted(glob.glob(resource_path('training_data/*.npz')))

        # Initialize hardware in background
        self._init_camera()
        self._init_ecs()
        self._init_systems()

        # Start game music based on exercise category
        if self.audio and self.templates:
            # Determine category from first template
            first_template = self.templates[0]
            category = self._get_category_from_template(first_template)
            music_track = self.audio.get_music_for_category(category)
            self.audio.play_music(music_track)


    def _get_category_from_template(self, template_path):
        """Determine exercise category from template filename."""
        import os
        filename = os.path.basename(template_path)

        # Arms exercises
        if filename in ["clap.npz", "parallel_arm_raise.npz", "lateral_raise.npz"]:
            return "arms"
        # Legs exercises
        elif filename in ["squat_rep.npz", "lateral_lunge.npz", "right_lunge.npz"]:
            return "legs"
        # Torso exercises
        elif filename in ["toe_touch.npz", "right_side_bend.npz", "lateral_hip_thrust.npz"]:
            return "torso"
        else:
            return "legs"  # Default to legs

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
        esper.add_processor(RepDetectionSystem(self.audio), priority=30)
        esper.add_processor(GameLogicSystem(self.audio), priority=20)
        esper.add_processor(RenderSystem(self.screen), priority=10)

    def check_ready(self):
        """Check if session is ready (webcam and assets)."""
        if not self.is_ready:
            # 1. Check webcam
            frame, landmarks = self.mp_thread.get_data()
            if frame is None:
                return False

            # 2. Check assets via RenderSystem
            render_sys = esper.get_processor(RenderSystem)
            if render_sys:
                # If we have no minigame yet, it's definitely not ready
                if render_sys.minigame is None:
                    # Trigger first process to create minigame
                    esper.process(0.016)
                    return False

                # Check for minigame specific assets
                mg = render_sys.minigame
                # For swimming: check if ocean is loaded
                if hasattr(mg, 'ocean_anim'):
                    if not mg.ocean_anim or len(mg.ocean_anim) == 0:
                        return False
                # For platformer: check if cloud is loaded
                elif hasattr(mg, 'cloud_img'):
                    if mg.cloud_img is None:
                        return False

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
