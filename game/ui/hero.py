"""Animated hero character using spritesheet."""
import pygame
from game.core.spritesheet import Spritesheet, AnimatedSprite


class Hero(AnimatedSprite):
    """The animated hero character for the title screen."""

    def __init__(self, x, y, sprite_width=512, sprite_height=512, columns=20, rows=19):
        """
        Create the hero character.

        Args:
            x: X position
            y: Y position
            sprite_width: Width of each sprite frame
            sprite_height: Height of each sprite frame
            columns: Number of columns in spritesheet
            rows: Number of rows in spritesheet
        """
        super().__init__(x, y)

        try:
            sheet = Spritesheet('game/data/hero_title_spritesheet.png')
            frames = sheet.get_sprites_grid(
                sprite_width, sprite_height,
                columns, rows,
                start_x=0, start_y=0,
                spacing_x=0, spacing_y=0
            )

            if frames:
                # Only use the first 375 frames (the rest are empty)
                frames = frames[:375]
                # Add idle animation at 30 fps, looping
                self.add_animation("idle", frames, fps=30, loop=True, is_default=True)
                print(f"Hero loaded with {len(frames)} frames")
            else:
                print("No frames loaded from hero spritesheet")
                self._create_placeholder_animation()

        except Exception as e:
            print(f"Error loading hero spritesheet: {e}")
            self._create_placeholder_animation()

        # Set default scale (can be adjusted)
        self.scale = 2.0

    def _create_placeholder_animation(self):
        """Create a placeholder animation if spritesheet fails to load."""
        # Create a simple animated placeholder
        placeholder_frames = []
        for i in range(4):
            frame = pygame.Surface((64, 64), pygame.SRCALPHA)
            # Animated color shift
            color_shift = int(50 + i * 40)
            frame.fill((color_shift, 100, 200, 255))

            # Draw a simple character shape
            pygame.draw.circle(frame, (255, 200, 100), (32, 20), 12)  # Head
            pygame.draw.rect(frame, (100, 150, 200), (22, 32, 20, 25))  # Body

            placeholder_frames.append(frame)

        self.add_animation("idle", placeholder_frames, fps=30, loop=True, is_default=True)


def create_hero(x, y):
    """
    Create a hero and try to auto-detect spritesheet dimensions.

    Args:
        x: X position
        y: Y position
        spritesheet_path: Path to spritesheet image

    Returns:
        Hero instance
    """

    width = 512
    height = 512
    cols = 20
    rows = 19

    hero = Hero(x, y, width, height, cols, rows)
    if hero.state_machine.current_state and len(hero.state_machine.animations) > 0:
        anim = hero.state_machine.animations[hero.state_machine.current_state]
        if len(anim.frames) > 0:
            first_frame = anim.frames[0]
            if first_frame.get_width() > 10 and first_frame.get_height() > 10:
                print(f"Auto-detected hero dimensions: {width}x{height}, {cols}x{rows}")
                return hero


def create_game_hero(x, y, animation_type="jump"):
    """
    Create a hero for in-game use with specific animations from hero_spritesheet.png.

    Animation frame ranges (1-indexed):
    - Frame 1: jump_idle
    - Frames 2-57: jump (56 frames) - for leg minigame
    - Frame 58: swim_idle
    - Frames 59-101: swim (43 frames) - for torso minigame
    - Frame 102: swing_idle
    - Frames 103-171: swing (69 frames) - for arms minigame

    Args:
        x: X position
        y: Y position
        animation_type: Type of animation ("jump", "swim", or "swing")

    Returns:
        AnimatedSprite with the specified animations
    """
    sprite = AnimatedSprite(x, y)

    try:
        sheet = Spritesheet('game/data/hero_spritesheet.png')

        # Spritesheet is 512x512 per frame, 20 columns x 19 rows = 380 total frames
        sprite_width = 512
        sprite_height = 512
        columns = 20
        rows = 19

        # Load animations based on type
        if animation_type == "jump":
            # Load jump idle (frame 1) - waiting for rep
            idle_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 1, 1)
            # Load jump prep/before release (frames 2-26) - preparing to jump
            prep_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 2, 21)
            # Load midair (frame 27) - at peak of jump
            midair_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 22, 22)
            # Load fall (frames 28-57) - falling down
            fall_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 23, 57)

            sprite.add_animation("idle", idle_frames, fps=30, loop=True, is_default=True)
            sprite.add_animation("jump_prep", prep_frames, fps=30, loop=False)  # Play once
            sprite.add_animation("midair", midair_frames, fps=30, loop=True)
            sprite.add_animation("fall", fall_frames, fps=30, loop=False)  # Play once
            print(f"Game hero loaded with jump animations ({len(prep_frames)} prep, 1 midair, {len(fall_frames)} fall frames)")

        elif animation_type == "swim":
            # Load swim idle (frame 58)
            idle_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 58, 58)
            # Load swim animation (frames 59-101)
            swim_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 59, 101)

            sprite.add_animation("idle", idle_frames, fps=30, loop=True, is_default=True)
            sprite.add_animation("swim", swim_frames, fps=30, loop=True)
            print(f"Game hero loaded with swim animations ({len(swim_frames)} swim frames)")

        elif animation_type == "swing":
            # Load swing idle (frame 102)
            idle_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 102, 102)
            # Load charge up / swing back (frames 103-125) - 23 frames
            charge_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 103, 125)
            # Load midair swing (frame 126) - 1 frame
            midair_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 126, 126)
            # Load swing catch (frames 127-171) - 45 frames
            catch_frames = sheet.get_frame_range(sprite_width, sprite_height, columns, rows, 127, 171)

            sprite.add_animation("idle", idle_frames, fps=30, loop=True, is_default=True)
            sprite.add_animation("charge", charge_frames, fps=30, loop=False)  # Don't loop
            sprite.add_animation("midair", midair_frames, fps=30, loop=True)
            sprite.add_animation("catch", catch_frames, fps=30, loop=False)  # Don't loop
            print(f"Game hero loaded with swing animations ({len(charge_frames)} charge, 1 midair, {len(catch_frames)} catch frames)")

        sprite.scale = 1.0  # Default scale

    except Exception as e:
        print(f"Error loading game hero animations: {e}")
        # Create placeholder
        placeholder_frame = pygame.Surface((64, 64), pygame.SRCALPHA)
        placeholder_frame.fill((100, 200, 255))
        sprite.add_animation("idle", [placeholder_frame], fps=30, loop=True, is_default=True)

    return sprite
