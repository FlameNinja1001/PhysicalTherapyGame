"""Swimming minigame - dash forward on each rep with camera follow (Torso exercises)."""
import pygame
import math
from game.ui import theme, hero, dynamic_camera

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

    def reset_reps(self):
        """Full reset - return to starting position."""
        self.player_world_x = 0
        self.camera.x = 0
        self.camera.target_x = 0
        self.total_distance = 0
        self.waves = []

    def reset_reps_only(self):
        """Reset only the rep tracking, keep player progress intact."""
        # Don't reset position or distance, player continues swimming
        pass

    def update(self, dt, rep_progress, rep_count):
        """Update minigame state."""
        # Swimming animation (continuous)
        self.swim_time += dt * 3
        self.arm_angle = math.sin(self.swim_time) * 25
        self.leg_kick = math.sin(self.swim_time * 1.5) * 15

        # Check for new rep (dash forward)
        expected_x = rep_count * self.dash_distance
        if self.player_world_x < expected_x - 10:
            if not self.is_dashing:
                self.is_dashing = True
                self.dash_progress = 0
                self.dash_start_x = self.player_world_x

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
                        'y': self.rect.height // 2 + (math.sin(self.swim_time) * 20),
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

    def draw(self):
        """Draw the swimming minigame."""
        # Background - ocean blue
        pygame.draw.rect(self.screen, (20, 80, 150), self.rect)

        # Draw water gradient
        for i in range(5):
            y = self.rect.y + i * (self.rect.height // 5)
            color_intensity = 20 + i * 10
            pygame.draw.rect(self.screen, (color_intensity, 80 + i * 5, 150 + i * 10),
                           (self.rect.x, y, self.rect.width, self.rect.height // 5))

        # Get camera offset and zoom
        camera_x, _ = self.camera.get_offset()
        zoom = self.camera.get_zoom()

        # Draw underwater objects (coral, rocks) - move with camera and parallax
        self._draw_underwater_scenery(camera_x, zoom)

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

        # Draw progress
        distance_text = f"Distance: {self.total_distance}m"
        text_surf = theme.FONTS['body'].render(distance_text, True, theme.WHITE)
        self.screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))

        # Dash indicator
        if self.is_dashing:
            dash_text = "DASH!"
            dash_surf = theme.FONTS['menu'].render(dash_text, True, theme.YELLOW)
            dash_rect = dash_surf.get_rect(center=(self.rect.centerx, self.rect.y + 50))
            self.screen.blit(dash_surf, dash_rect)

    def _draw_underwater_scenery(self, camera_x, zoom):
        """Draw scrolling underwater scenery with parallax and zoom."""
        # Coral and rocks at intervals (closer to camera, moves at full speed)
        for i in range(-2, 15):
            world_x = i * 250
            screen_offset_x = (world_x - camera_x) * zoom
            screen_x = self.rect.x + int(screen_offset_x)

            if screen_x < self.rect.x - 100 or screen_x > self.rect.x + self.rect.width + 100:
                continue

            # Coral (triangle-ish) with zoom
            coral_y = self.rect.y + int((self.rect.height - 80) * zoom)
            coral_points = [
                (screen_x, coral_y - int(40 * zoom)),
                (screen_x - int(20 * zoom), coral_y),
                (screen_x + int(20 * zoom), coral_y)
            ]
            pygame.draw.polygon(self.screen, (200, 100, 150), coral_points)

            # Small rock with zoom
            rock_x = screen_x + int(100 * zoom)
            rock_y = self.rect.y + int((self.rect.height - 60) * zoom)
            pygame.draw.ellipse(self.screen, (100, 100, 100),
                              (rock_x - int(25 * zoom), rock_y - int(15 * zoom),
                               int(50 * zoom), int(30 * zoom)))

        # Seaweed (wavy lines) with parallax (background layer at 0.7 speed)
        parallax_factor = 0.7
        for i in range(-1, 12):
            world_x = i * 300 + 150
            screen_offset_x = (world_x - camera_x * parallax_factor) * zoom
            screen_x = self.rect.x + int(screen_offset_x)

            if screen_x < self.rect.x - 50 or screen_x > self.rect.x + self.rect.width + 50:
                continue

            # Draw wavy seaweed with zoom
            base_y = self.rect.y + int((self.rect.height - 50) * zoom)
            wave_offset = math.sin(self.swim_time + i) * 10 * zoom

            points = []
            for j in range(8):
                y = base_y - int(j * 10 * zoom)
                x = screen_x + int(math.sin(self.swim_time * 2 + i + j * 0.5) * wave_offset)
                points.append((x, y))

            if len(points) > 1:
                pygame.draw.lines(self.screen, (50, 150, 80), False, points, max(1, int(3 * zoom)))

