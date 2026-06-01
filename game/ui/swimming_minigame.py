"""Swimming minigame - dash forward on each rep with camera follow (Torso exercises)."""
import pygame
import math
from game.ui import theme, hero, dynamic_camera
from game.core.spritesheet import Spritesheet
from game.core.paths import resource_path

class SwimmingMinigame:
    """Player swims continuously, dashing forward on each rep."""

    def __init__(self, screen, x, y, width, height):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)

        # Player state
        self.player_world_x = 0  # Player position in world space

        # Dynamic camera with zoom
        self.camera = dynamic_camera.DynamicCamera()
        self.camera.idle_zoom = 1.0
        self.camera.action_zoom = 1.2  # Zoom in during dash
        self.camera.follow_speed = 5.0
        self.camera.zoom_speed = 2.5

        # Swimming animation
        self.swim_time = 0
        self.arm_angle = 0
        self.leg_kick = 0

        # Dashing state
        self.is_dashing = False
        self.dash_progress = 0
        self.dash_start_x = 0
        self.dash_distance = 200  # Distance per rep
        self.last_rep_count = 0  # Track previous rep count to detect new reps
        self.base_position = 0  # Base position offset for continuous progress across exercises

        # Wave particles for effect
        self.waves = []
        self.wave_spawn_timer = 0

        # Total distance swum
        self.total_distance = 0

        # Load animated hero with swim animation
        self.hero_sprite = hero.create_game_hero(0, 0, "swim")
        self.hero_sprite.scale = 0.25  # Scale to ~128px
        self.hero_offset_x = -60  # Offset left to center
        self.hero_offset_y = -60  # Offset up to center vertically

        # Load ocean water animation (39 frames, 20 columns, 2 rows)
        try:
            ocean_sheet = Spritesheet(resource_path('game/data/ocean_spritesheet.png'))
            # Get first frame to determine sprite size
            sheet_width = ocean_sheet.sheet.get_width()
            sheet_height = ocean_sheet.sheet.get_height()
            sprite_width = sheet_width // 20  # 20 columns
            sprite_height = sheet_height // 2  # 2 rows
            self.ocean_frames = ocean_sheet.get_sprites_grid(
                sprite_width, sprite_height, 20, 2,
                start_x=0, start_y=0, spacing_x=0, spacing_y=0
            )
            # Only use first 39 frames
            self.ocean_frames = self.ocean_frames[:39]
            self.ocean_frame_index = 0
            self.ocean_anim_time = 0
            print(f"Ocean animation loaded: {len(self.ocean_frames)} frames at {sprite_width}x{sprite_height}")
        except Exception as e:
            print(f"Warning: Could not load ocean animation: {e}")
            self.ocean_frames = None

        # Load ocean gradient overlay
        try:
            self.ocean_gradient = pygame.image.load(resource_path('game/data/ocean_gradient.png')).convert_alpha()
            print(f"Ocean gradient loaded: {self.ocean_gradient.get_width()}x{self.ocean_gradient.get_height()}")
        except Exception as e:
            print(f"Warning: Could not load ocean gradient: {e}")
            self.ocean_gradient = None

    def reset_reps(self):
        """Full reset - return to starting position."""
        self.player_world_x = 0
        self.camera.x = 0
        self.camera.target_x = 0
        self.total_distance = 0
        self.waves = []
        self.last_rep_count = 0
        self.base_position = 0

    def reset_reps_only(self):
        """Reset only the rep tracking, keep player progress intact."""
        # Save current position as base for next exercise
        self.base_position = self.player_world_x
        # Reset rep tracking so new exercise can detect reps
        self.last_rep_count = 0

    def update(self, dt, rep_progress, rep_count):
        """Update minigame state."""
        # Swimming animation (continuous)
        self.swim_time += dt * 3
        self.arm_angle = math.sin(self.swim_time) * 25
        self.leg_kick = math.sin(self.swim_time * 1.5) * 15

        # Check for new rep (dash forward) - detect NEW rep, not absolute count
        if rep_count > self.last_rep_count:
            if not self.is_dashing:
                self.is_dashing = True
                self.dash_progress = 0
                self.dash_start_x = self.player_world_x
            self.last_rep_count = rep_count

        # Calculate expected position (base_position + reps from current exercise)
        expected_x = self.base_position + (rep_count * self.dash_distance)

        # Update dash
        if self.is_dashing:
            # Swim animation: 43 frames @ 30fps = 1.43 seconds
            # Dash speed should complete in animation time
            dash_duration = 43 / 30.0  # 1.43 seconds
            self.dash_progress += dt / dash_duration
            if self.dash_progress >= 1.0:
                self.dash_progress = 1.0
                self.is_dashing = False
                self.player_world_x = expected_x
            else:
                # Smooth dash with ease out
                t = 1 - (1 - self.dash_progress) ** 3  # Ease out cubic
                self.player_world_x = self.dash_start_x + (expected_x - self.dash_start_x) * t

                # Spawn wave particles during dash
                self.wave_spawn_timer += dt
                if self.wave_spawn_timer > 0.05:
                    self.wave_spawn_timer = 0
                    self.waves.append({
                        'x': self.player_world_x - 30,
                        'y': self.rect.height // 2 + 20,
                        'life': 1.0,
                        'size': 15
                    })

        # Update camera to follow player with zoom
        target_camera_x = self.player_world_x - 150  # Player offset from left edge
        self.camera.set_target(target_camera_x, 0)
        self.camera.set_moving(self.is_dashing)
        self.camera.update(dt)

        # Update wave particles
        for wave in self.waves[:]:
            wave['life'] -= dt * 2
            wave['size'] += dt * 30
            if wave['life'] <= 0:
                self.waves.remove(wave)

        self.total_distance = int(self.player_world_x)

        # Update hero animation
        self.hero_sprite.update(dt)

        # Switch to swim animation when dashing, idle when not
        if self.is_dashing:
            self.hero_sprite.set_animation("swim", reset=False)
        else:
            self.hero_sprite.set_animation("idle", reset=False)

        # Update ocean animation (30 fps)
        if self.ocean_frames:
            self.ocean_anim_time += dt
            frame_duration = 1.0 / 30.0
            if self.ocean_anim_time >= frame_duration:
                self.ocean_anim_time -= frame_duration
                self.ocean_frame_index = (self.ocean_frame_index + 1) % len(self.ocean_frames)

    def draw(self):
        """Draw the swimming minigame."""
        # Set clipping to keep everything within bounds
        self.screen.set_clip(self.rect)

        # Get camera offset and zoom FIRST
        camera_x, _ = self.camera.get_offset()
        zoom = self.camera.get_zoom()

        # Draw smooth gradient background for night sky/water (darkish blue, 60% opacity)
        self._draw_smooth_gradient(zoom)

        # Draw animated ocean water
        self._draw_ocean_water(zoom, camera_x)

        # Draw peach-ish ground at bottom
        ground_height = int(80 * zoom)
        ground_y = self.rect.y + self.rect.height - ground_height
        # Peach color gradient - lighter at top, darker at bottom
        for i in range(ground_height):
            t = i / ground_height
            r = int(255 - t * 40)  # 255 -> 215
            g = int(218 - t * 40)  # 218 -> 178
            b = int(185 - t * 40)  # 185 -> 145
            pygame.draw.line(self.screen, (r, g, b),
                           (self.rect.x, ground_y + i),
                           (self.rect.x + self.rect.width, ground_y + i))

        # Draw wave particles with zoom
        for wave in self.waves:
            alpha = int(wave['life'] * 150)
            if alpha > 0:
                screen_offset_x = (wave['x'] - camera_x) * zoom
                screen_x = self.rect.x + int(screen_offset_x)
                screen_y = self.rect.y + int(wave['y'] * zoom)

                if 0 <= screen_x < self.rect.x + self.rect.width:
                    # Draw wave circle with zoom
                    size = int(wave['size'] * zoom)
                    wave_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(wave_surf, (255, 255, 255, alpha),
                                     (size, size), size, max(1, int(2 * zoom)))
                    self.screen.blit(wave_surf, (screen_x - size, screen_y - size))

        # Draw animated hero with zoom
        player_screen_x = self.rect.x + int(150 * zoom)  # Fixed position on screen with zoom
        player_screen_y = self.rect.y + int((self.rect.height // 2 + math.sin(self.swim_time) * 3) * zoom)

        self.hero_sprite.x = player_screen_x + self.hero_offset_x
        self.hero_sprite.y = player_screen_y + self.hero_offset_y
        self.hero_sprite.scale = 0.25 * zoom  # Scale hero with zoom
        self.hero_sprite.draw(self.screen)

        # Reset clipping
        self.screen.set_clip(None)

    def _draw_smooth_gradient(self, zoom):
        """Draw a smooth gradient background (brighter night sky for underwater scene)."""
        # Create a surface with alpha for the gradient (same size regardless of zoom)
        gradient_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Brighter blue night colors for better visibility with transparent water
        top_color = (45, 56, 74)  # Brighter sky blue
        bottom_color = (0, 23, 61)  # Lighter ocean blue

        # Draw many lines for smooth gradient
        for i in range(self.rect.height):
            t = i / self.rect.height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            # Full opacity for base gradient
            pygame.draw.line(gradient_surf, (r, g, b, 255), (0, i), (self.rect.width, i))

        self.screen.blit(gradient_surf, (self.rect.x, self.rect.y))

    def _draw_ocean_water(self, zoom, camera_x):
        """Draw animated ocean water sprite with zoom and transparency."""
        if not self.ocean_frames or len(self.ocean_frames) == 0:
            return

        # Get current frame
        current_frame = self.ocean_frames[self.ocean_frame_index]

        # Scale water to fit the width of the minigame area AND apply zoom
        water_target_width = int(self.rect.width * zoom)
        water_aspect = current_frame.get_width() / current_frame.get_height()
        water_target_height = int(water_target_width / water_aspect)

        scaled_water = pygame.transform.smoothscale(current_frame, (water_target_width, water_target_height))

        # Apply 70% opacity (179 alpha out of 255)
        scaled_water_with_alpha = scaled_water.copy()
        scaled_water_with_alpha.set_alpha(179)

        # Position water in lower portion of the screen (above ground) with zoom
        ground_height = int(80 * zoom)
        water_y = self.rect.y + self.rect.height - ground_height - water_target_height

        # Apply horizontal camera offset for scrolling effect
        water_x = self.rect.x - int((camera_x * zoom) % water_target_width)

        # Draw multiple tiles if needed to cover the width
        while water_x < self.rect.x + self.rect.width:
            self.screen.blit(scaled_water_with_alpha, (water_x, water_y))
            water_x += water_target_width

        # Draw ocean gradient overlay on top
        if self.ocean_gradient:
            # Scale gradient to match water size
            scaled_gradient = pygame.transform.smoothscale(self.ocean_gradient, (water_target_width, water_target_height))

            # Draw gradient tiles on top of water
            gradient_x = self.rect.x - int((camera_x * zoom) % water_target_width)
            while gradient_x < self.rect.x + self.rect.width:
                self.screen.blit(scaled_gradient, (gradient_x, water_y))
                gradient_x += water_target_width
