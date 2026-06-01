import esper
import random
import os
import pygame
from game.components.camera import CameraFrameComponent
from game.components.pose import PoseLandmarksComponent, JointAnglesComponent
from game.components.exercise import ExerciseComponent, RepStateComponent
from game.components.game_state import GameStateComponent
from game.ui import theme, game_hud, platformer, webcam_view, demo_video_player, jungle_minigame, swimming_minigame

NICE_MESSAGES = [
    "Nice!",
    "Excellent!",
    "Beautiful!",
    "Brilliant!",
    "Great!",
    "Awesome!",
    "Good!",
    "Groovy!",
    "Sweet!"
]

class RenderSystem(esper.Processor):
    """Orchestrates rendering of all game UI components."""

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.hud = game_hud.GameHUD(screen)
        self.minigame = None  # Will be set dynamically based on exercise
        self.current_category = None  # Track current minigame category
        self.webcam_view = webcam_view.WebcamView(screen)
        self.demo_player = demo_video_player.DemoVideoPlayer(screen)
        self.last_rep_count = 0
        self.current_exercise_path = ""

    def _get_exercise_category(self, exercise_path):
        """Determine exercise category from filename."""
        filename = os.path.basename(exercise_path)

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

    def _create_minigame_for_category(self, category, sw, sh):
        """Create appropriate minigame based on exercise category."""
        x, y, w, h = sw // 2, 0, sw // 2, sh

        if category == "arms":
            return jungle_minigame.JungleMinigame(self.screen, x, y, w, h)
        elif category == "legs":
            return platformer.PlatformerMinigame(self.screen, x, y, w, h)
        elif category == "torso":
            return swimming_minigame.SwimmingMinigame(self.screen, x, y, w, h)
        else:
            return platformer.PlatformerMinigame(self.screen, x, y, w, h)

    def process(self, dt=0.016):
        """Main rendering loop - orchestrates all visual components."""
        # Update minigame dimensions based on screen size
        sw, sh = self.screen.get_size()

        for ent, (cam, pose, rep, state, ex, angles) in esper.get_components(
                CameraFrameComponent, PoseLandmarksComponent,
                RepStateComponent, GameStateComponent, ExerciseComponent, JointAnglesComponent):

            if cam.frame is None:
                continue

            # Handle exercise changes
            if ex.template_path != self.current_exercise_path:
                self.last_rep_count = 0

                # Determine exercise category
                category = self._get_exercise_category(ex.template_path)

                # Only create new minigame if category changed, otherwise just reset reps
                if category != self.current_category or self.minigame is None:
                    # Category changed - create new minigame
                    self.minigame = self._create_minigame_for_category(category, sw, sh)
                    self.current_category = category
                else:
                    # Same category - just reset rep count, keep progress
                    if hasattr(self.minigame, 'reset_reps_only'):
                        self.minigame.reset_reps_only()

                self.demo_player.set_exercise(ex.template_path)
                self.current_exercise_path = ex.template_path

            # Update minigame dimensions
            if self.minigame:
                self.minigame.rect = pygame.Rect(sw // 2, 0, sw // 2, sh)

            # Update all sub-components
            self.hud.update(dt)
            if self.minigame:
                self.minigame.update(dt, rep.progress, rep.rep_count)
            self.demo_player.update(dt)

            # Check for new rep feedback
            if rep.rep_count > self.last_rep_count:
                self.hud.set_feedback(random.choice(NICE_MESSAGES).upper(), theme.ACCENT)
                self.last_rep_count = rep.rep_count
            elif rep.deviation > ex.dev_thresh and rep.progress > 0.1:
                # TODO: recurring feedback for poor form
                pass

            # Clear background
            self.screen.fill(theme.BACKGROUND)

            # Draw components in layers
            self.webcam_view.draw(cam.frame, pose.landmarks, is_locked=rep.is_locked)
            if self.minigame:
                self.minigame.draw()
            self.demo_player.draw()

            # Get minigame stat for HUD
            minigame_stat = 0
            if self.minigame:
                if hasattr(self.minigame, 'total_height_climbed'):
                    minigame_stat = self.minigame.total_height_climbed
                elif hasattr(self.minigame, 'current_tree'):
                    minigame_stat = self.minigame.current_tree + 1
                elif hasattr(self.minigame, 'total_distance'):
                    minigame_stat = self.minigame.total_distance

            minigame_type_map = {
                "arms": "jungle",
                "legs": "platformer",
                "torso": "swimming"
            }
            minigame_type = minigame_type_map.get(self.current_category, "platformer")

            self.hud.draw(state, rep, ex, minigame_stat, minigame_type)
