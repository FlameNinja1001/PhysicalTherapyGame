"""Spritesheet loading and animation system."""
import pygame
from typing import Dict, List, Tuple


class Spritesheet:
    """Load and parse sprite sheets."""

    def __init__(self, image_path):
        """Load a spritesheet image."""
        try:
            self.sheet = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Unable to load spritesheet: {image_path}")
            # Create a placeholder surface
            self.sheet = pygame.Surface((100, 100), pygame.SRCALPHA)
            self.sheet.fill((255, 0, 255))  # Magenta for missing texture

    def get_sprite(self, x, y, width, height):
        """Extract a single sprite from the sheet."""
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        return sprite

    def get_sprites_grid(self, sprite_width, sprite_height, columns, rows, start_x=0, start_y=0, spacing_x=0, spacing_y=0):
        """
        Extract a grid of sprites from the sheet.

        Args:
            sprite_width: Width of each sprite
            sprite_height: Height of each sprite
            columns: Number of columns
            rows: Number of rows
            start_x: Starting x offset
            start_y: Starting y offset
            spacing_x: Horizontal spacing between sprites
            spacing_y: Vertical spacing between sprites

        Returns:
            List of sprite surfaces
        """
        sprites = []
        for row in range(rows):
            for col in range(columns):
                x = start_x + col * (sprite_width + spacing_x)
                y = start_y + row * (sprite_height + spacing_y)
                sprite = self.get_sprite(x, y, sprite_width, sprite_height)
                sprites.append(sprite)
        return sprites

    def get_frame_range(self, sprite_width, sprite_height, columns, rows, start_frame, end_frame, spacing_x=0, spacing_y=0):
        """
        Extract a range of frames from a spritesheet grid.

        Args:
            sprite_width: Width of each sprite
            sprite_height: Height of each sprite
            columns: Number of columns in the grid
            rows: Number of rows in the grid
            start_frame: Starting frame (1-indexed)
            end_frame: Ending frame (1-indexed, inclusive)
            spacing_x: Horizontal spacing between sprites
            spacing_y: Vertical spacing between sprites

        Returns:
            List of sprite surfaces for the specified frame range
        """
        # Get all sprites first
        all_sprites = self.get_sprites_grid(sprite_width, sprite_height, columns, rows, 0, 0, spacing_x, spacing_y)

        # Convert to 0-indexed and extract range (end_frame is inclusive)
        start_idx = start_frame - 1
        end_idx = end_frame  # end_frame is inclusive, so we don't subtract 1

        return all_sprites[start_idx:end_idx]


class Animation:
    """Represents a single animation sequence."""

    def __init__(self, frames: List[pygame.Surface], fps: float = 30, loop: bool = True):
        """
        Create an animation.

        Args:
            frames: List of sprite surfaces
            fps: Frames per second
            loop: Whether animation should loop
        """
        self.frames = frames
        self.fps = fps
        self.frame_duration = 1.0 / fps if fps > 0 else 0.1
        self.loop = loop
        self.current_frame = 0
        self.time_accumulator = 0.0
        self.finished = False

    def update(self, dt: float):
        """Update animation state."""
        if self.finished and not self.loop:
            return

        self.time_accumulator += dt

        while self.time_accumulator >= self.frame_duration:
            self.time_accumulator -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True

    def get_current_frame(self) -> pygame.Surface:
        """Get the current frame surface."""
        if not self.frames:
            # Return a placeholder
            placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))
            return placeholder
        return self.frames[self.current_frame]

    def reset(self):
        """Reset animation to start."""
        self.current_frame = 0
        self.time_accumulator = 0.0
        self.finished = False


class AnimationStateMachine:
    """Manage multiple animations with state transitions."""

    def __init__(self):
        """Initialize the state machine."""
        self.animations: Dict[str, Animation] = {}
        self.current_state: str = None
        self.default_state: str = None

    def add_animation(self, state_name: str, animation: Animation, is_default: bool = False):
        """
        Add an animation state.

        Args:
            state_name: Name of the state
            animation: Animation object
            is_default: Whether this is the default/initial state
        """
        self.animations[state_name] = animation
        if is_default or self.default_state is None:
            self.default_state = state_name
            if self.current_state is None:
                self.current_state = state_name

    def set_state(self, state_name: str, reset: bool = True):
        """
        Change to a different animation state.

        Args:
            state_name: Name of the state to transition to
            reset: Whether to reset the animation to frame 0
        """
        if state_name in self.animations:
            self.current_state = state_name
            if reset:
                self.animations[state_name].reset()

    def update(self, dt: float):
        """Update current animation."""
        if self.current_state and self.current_state in self.animations:
            self.animations[self.current_state].update(dt)

    def get_current_frame(self) -> pygame.Surface:
        """Get current frame from active animation."""
        if self.current_state and self.current_state in self.animations:
            return self.animations[self.current_state].get_current_frame()

        # Return placeholder if no state
        placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
        placeholder.fill((255, 0, 255))
        return placeholder

    def is_finished(self) -> bool:
        """Check if current animation has finished (for non-looping animations)."""
        if self.current_state and self.current_state in self.animations:
            return self.animations[self.current_state].finished
        return False


class AnimatedSprite:
    """A sprite with animation state machine."""

    def __init__(self, x: float = 0, y: float = 0):
        """
        Create an animated sprite.

        Args:
            x: Initial x position
            y: Initial y position
        """
        self.x = x
        self.y = y
        self.state_machine = AnimationStateMachine()
        self.scale = 1.0
        self.flip_x = False
        self.flip_y = False

    def update(self, dt: float):
        """Update animation."""
        self.state_machine.update(dt)

    def draw(self, screen: pygame.Surface, camera_x: float = 0, camera_y: float = 0):
        """
        Draw the sprite.

        Args:
            screen: Pygame surface to draw on
            camera_x: Camera x offset
            camera_y: Camera y offset
        """
        frame = self.state_machine.get_current_frame()

        # Apply transformations
        if self.flip_x or self.flip_y or self.scale != 1.0:
            # Flip
            if self.flip_x or self.flip_y:
                frame = pygame.transform.flip(frame, self.flip_x, self.flip_y)

            # Scale
            if self.scale != 1.0:
                new_w = int(frame.get_width() * self.scale)
                new_h = int(frame.get_height() * self.scale)
                frame = pygame.transform.smoothscale(frame, (new_w, new_h))

        # Draw at position with camera offset
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        screen.blit(frame, (screen_x, screen_y))

    def set_animation(self, state_name: str, reset: bool = True):
        """Change animation state."""
        self.state_machine.set_state(state_name, reset)

    def add_animation(self, state_name: str, frames: List[pygame.Surface], fps: float = 30, loop: bool = True, is_default: bool = False):
        """Add an animation to this sprite."""
        animation = Animation(frames, fps, loop)
        self.state_machine.add_animation(state_name, animation, is_default)
