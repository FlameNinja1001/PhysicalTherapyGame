import pygame
import math
import random
from game.ui import theme, animations, hero, dynamic_camera
from game.core.paths import resource_path

class PlatformerMinigame:
    def __init__(self, screen, x, y, width, height):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)

        # Load cloud sprite and scale to reasonable size while preserving aspect ratio
        try:
            cloud_orig = pygame.image.load(resource_path('game/data/cloud.png')).convert_alpha()
            # Scale down to 1/4 size (1024x452 -> 256x113) preserving aspect ratio
            cloud_scale = 0.25  # Scale factor
            target_width = int(cloud_orig.get_width() * cloud_scale)
            target_height = int(cloud_orig.get_height() * cloud_scale)
            self.cloud_img = pygame.transform.smoothscale(cloud_orig, (target_width, target_height))
            self.cloud_scale = cloud_scale  # Store for reference
            print(f"Cloud loaded and scaled: {self.cloud_img.get_width()}x{self.cloud_img.get_height()}")
        except:
            print("Warning: Could not load cloud.png, using placeholder")
            self.cloud_img = None
            self.cloud_scale = 1.0

        # Player state
        self.player_pos = pygame.Vector2(x + width // 2, y + height)
        self.player_vel = pygame.Vector2(0, 0)
        self.is_jumping = False
        self.is_winding_up = False  # True during windup, before actual jump
        self.jump_start_time = 0  # Track time in jump for animation states
        self.gravity = 600
        self.jump_force = -500

        # Dynamic camera without zoom to prevent snapping
        self.camera = dynamic_camera.DynamicCamera()
        self.camera.idle_zoom = 1.0
        self.camera.action_zoom = 1.0  # No zoom - keeps movement smooth
        self.camera.follow_speed = 6.0  # Very fast to stay with player
        self.camera.zoom_speed = 10.0  # Instant (not used since zoom is disabled)

        # World state
        self.platforms = []
        self.last_rep_count = 0
        self.current_platform_idx = 0  # Track actual platform player is on
        self.total_height_climbed = 0  # Cumulative high score
        self.initial_player_y = y + height
        self.platform_spacing = 150  # Reduced spacing for easier jumps
        self.next_platform_y = y + height - 100  # Y position for next platform

        # Generate initial vertical platforms
        for i in range(30):
            self._spawn_platform(i)

        # Load animated hero with jump animation
        self.hero_sprite = hero.create_game_hero(0, 0, "jump")
        self.hero_sprite.scale = 0.25  # Scale to ~128px
        self.hero_offset_x = -60  # Offset left to center better
        self.hero_offset_y = -30  # Offset up so feet align with platform

    def _spawn_platform(self, index):
        """Spawn a new platform at the next available position"""
        # Make platform hitbox match cloud image size if available
        if self.cloud_img:
            pw, ph = self.cloud_img.get_width(), self.cloud_img.get_height()
        else:
            pw, ph = 150, 20

        # FIXED positions - no randomization for predictable jumps
        px = self.rect.x + 150 + (index % 2) * 220  # Alternating left/right pattern
        py = self.next_platform_y - index * self.platform_spacing
        self.platforms.append(pygame.Rect(px, py, pw, ph))

    def update(self, dt, rep_progress, rep_count):
        # 0. Generate new platforms ahead of player
        if len(self.platforms) > 0:
            highest_platform = self.platforms[-1]
            # If player is getting close to the highest platform, spawn more
            if self.player_pos.y < highest_platform.y + 1000:
                for i in range(10):
                    new_index = len(self.platforms)
                    self._spawn_platform(new_index)


        # 1. Trigger Jump Windup on Rep Completion
        if rep_count > self.last_rep_count:
            # Calculate height climbed (distance between platforms)
            old_idx = self.current_platform_idx
            new_idx = self.current_platform_idx + 1
            if new_idx < len(self.platforms):
                height_gain = abs(self.platforms[old_idx].y - self.platforms[new_idx].y)
                self.total_height_climbed += height_gain
                self.current_platform_idx = new_idx

            self.last_rep_count = rep_count
            self.is_winding_up = True  # Start windup, NOT jumping yet
            self.jump_start_time = 0  # Reset timer

            # Get target platform for direction
            target_p = self.platforms[min(self.current_platform_idx, len(self.platforms) - 1)]

            # Flip player to face the next platform
            if target_p.centerx < self.player_pos.x:
                self.hero_sprite.flip_x = True  # Face left
            else:
                self.hero_sprite.flip_x = False  # Face right

            # Start jump prep animation (frames 2-26)
            self.hero_sprite.set_animation("jump_prep", reset=True)

        # 2. Windup Phase - NO physics yet, just animation
        if self.is_winding_up:
            self.jump_start_time += dt

            # Windup duration: 25 frames at 30fps = 0.83 seconds
            prep_duration = 25 / 30.0

            if self.jump_start_time >= prep_duration:
                # Windup complete - NOW start the actual jump!
                self.is_winding_up = False
                self.is_jumping = True
                self.jump_start_time = 0  # Reset for jump phase

                target_p = self.platforms[min(self.current_platform_idx, len(self.platforms) - 1)]

                # Calculate actual physics airtime for the jump
                actual_airtime = 1.4 * abs(self.jump_force) / self.gravity

                self.player_vel.y = self.jump_force  # Launch!
                self.player_vel.x = (target_p.centerx - self.player_pos.x) / actual_airtime

                # Transition to midair animation
                self.hero_sprite.set_animation("midair", reset=True)

        # 3. Jump Physics - ONLY when actually jumping (after windup)
        elif self.is_jumping:
            # Track jump time
            self.jump_start_time += dt

            # Apply gravity
            self.player_vel.y += self.gravity * dt
            # Update position
            self.player_pos += self.player_vel * dt

            # Animation state management based on velocity
            # midair: frame 27 (when going up)
            # fall: frames 28-57 (when falling down)

            if self.player_vel.y < 0:
                # Going up - show midair
                if self.hero_sprite.state_machine.current_state != "midair":
                    self.hero_sprite.set_animation("midair", reset=True)
            else:
                # Falling down - show fall animation
                if self.hero_sprite.state_machine.current_state != "fall":
                    self.hero_sprite.set_animation("fall", reset=True)

            # Check for natural landing
            target_p = self.platforms[min(self.current_platform_idx, len(self.platforms) - 1)]
            target_y = target_p.top - 40

            # Simple landing: just stop when we reach the target height while falling
            if self.player_vel.y > 0 and abs(self.player_pos.y - target_y) < 5:
                # Natural landing - just stop motion
                self.player_pos.y = target_y
                # Keep X position where physics naturally landed - no snapping!
                self.player_vel = pygame.Vector2(0, 0)
                self.is_jumping = False
                self.hero_sprite.set_animation("idle", reset=True)
        else:
            # While waiting for rep, smoothly stay on current platform
            target_p = self.platforms[min(self.current_platform_idx, len(self.platforms) - 1)]
            target_y = target_p.top - 40
            target_x = target_p.centerx

            # Smooth positioning (helps with any floating point drift)
            self.player_pos.y += (target_y - self.player_pos.y) * 10 * dt
            self.player_pos.x += (target_x - self.player_pos.x) * 10 * dt

        # 3. Camera Follow with zoom
        # Follow player's Y position vertically
        target_camera_y = self.player_pos.y - (self.rect.y + self.rect.height // 2)
        self.camera.set_target(0, target_camera_y)
        self.camera.set_moving(self.is_jumping)
        self.camera.update(dt)

        # 4. Update hero animation
        self.hero_sprite.update(dt)

    def reset_reps(self):
        """Full reset - return to starting position."""
        self.last_rep_count = 0
        self.current_platform_idx = 0
        self.player_pos = pygame.Vector2(self.rect.x + self.rect.width // 2, self.initial_player_y)
        self.player_vel = pygame.Vector2(0, 0)
        self.is_jumping = False
        self.is_winding_up = False
        self.camera.y = 0
        self.camera.target_y = 0
        # Optionally reset total_height_climbed if you want full restart
        # self.total_height_climbed = 0

    def reset_reps_only(self):
        """Reset rep count but keep player position and cumulative height."""
        self.last_rep_count = 0
        # Don't reset position or height - player continues climbing from current location

    def draw(self):
        # Clip area for platformer
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.rect)

        # Get camera offset and zoom
        _, camera_y = self.camera.get_offset()
        zoom = self.camera.get_zoom()

        # Draw gradient sky background (light blue to darker blue) with parallax
        self._draw_sky_gradient(camera_y, zoom)

        # Draw clouds (platforms) with vertical scroll and zoom
        for i, p in enumerate(self.platforms):
            # Apply camera offset and zoom
            screen_y = int((p.y - camera_y) * zoom) + self.rect.y
            screen_x = int((p.x - self.rect.x) * zoom) + self.rect.x
            screen_w = int(p.width * zoom)
            screen_h = int(p.height * zoom)

            cloud_rect = pygame.Rect(screen_x, screen_y, screen_w, screen_h)

            if self.rect.colliderect(cloud_rect):
                self._draw_cloud(cloud_rect, i < self.current_platform_idx, zoom)

        # Draw animated hero with zoom
        px = self.player_pos.x
        py = int((self.player_pos.y - camera_y) * zoom) + self.rect.y

        self.hero_sprite.x = px + self.hero_offset_x
        self.hero_sprite.y = py + self.hero_offset_y
        self.hero_sprite.scale = 0.25 * zoom  # Scale hero with zoom
        self.hero_sprite.draw(self.screen)

        self.screen.set_clip(old_clip)

    def _draw_sky_gradient(self, camera_y, zoom):
        """Draw a gradient sky background from light to dark blue (static, no parallax)."""
        # Light blue at top, darker blue at bottom
        top_color = (135, 206, 250)  # Light sky blue
        bottom_color = (70, 130, 180)  # Steel blue

        # Draw static gradient - no camera offset
        num_steps = 50
        for i in range(num_steps):
            t = i / num_steps
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)

            y = self.rect.y + int(i * self.rect.height / num_steps)
            height = int(self.rect.height / num_steps) + 1
            pygame.draw.rect(self.screen, (r, g, b), (self.rect.x, y, self.rect.width, height))

    def _draw_cloud(self, cloud_rect, is_completed, zoom):
        """Draw a cloud platform."""
        if self.cloud_img:
            # Scale cloud with zoom
            if zoom != 1.0:
                scaled_cloud = pygame.transform.smoothscale(self.cloud_img,
                    (int(self.cloud_img.get_width() * zoom), int(self.cloud_img.get_height() * zoom)))
            else:
                scaled_cloud = self.cloud_img

            # Center cloud image on platform rect
            cloud_x = cloud_rect.centerx - scaled_cloud.get_width() // 2
            cloud_y = cloud_rect.centery - scaled_cloud.get_height() // 2

            # Tint completed clouds slightly - preserve alpha by using multiply blend
            if is_completed:
                # Create a copy and apply yellow tint while preserving alpha
                tinted_cloud = scaled_cloud.copy()
                # Create a yellow overlay surface with per-pixel alpha
                overlay = pygame.Surface(tinted_cloud.get_size(), pygame.SRCALPHA)
                overlay.fill((255, 255, 200, 80))  # Light yellow with transparency
                tinted_cloud.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(tinted_cloud, (cloud_x, cloud_y))
            else:
                self.screen.blit(scaled_cloud, (cloud_x, cloud_y))
        else:
            # Fallback to drawing simple cloud shape if image not loaded
            color = (255, 255, 255) if not is_completed else (255, 255, 200)
            # Draw 3 overlapping circles to form a cloud with zoom
            pygame.draw.circle(self.screen, color, (cloud_rect.centerx - int(20 * zoom), cloud_rect.centery), int(15 * zoom))
            pygame.draw.circle(self.screen, color, (cloud_rect.centerx, cloud_rect.centery - int(10 * zoom)), int(20 * zoom))
            pygame.draw.circle(self.screen, color, (cloud_rect.centerx + int(20 * zoom), cloud_rect.centery), int(15 * zoom))
