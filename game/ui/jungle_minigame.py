"""Jungle minigame - swing from tree to tree on each rep (Arms exercises)."""
import pygame
import math
import random
from game.ui import theme, animations, hero, dynamic_camera


class JungleMinigame:
    """Player swings from tree to tree - each rep advances to the next tree."""

    def __init__(self, screen, x, y, width, height):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)

        # Load tree sprites and scale them down (original is 512x512, scale to ~1/4)
        scale_factor = 0.25  # Scale down to 128px from 512px
        leaves_scale_factor = 0.5  # Leaves are bigger - 180px

        trunk_base_orig = pygame.image.load('game/data/trunk_base.png').convert_alpha()
        trunk_orig = pygame.image.load('game/data/trunk.png').convert_alpha()
        leaves_orig = pygame.image.load('game/data/leaves.png').convert_alpha()

        trunk_size = int(512 * scale_factor)
        leaves_size = int(512 * leaves_scale_factor)
        self.trunk_base_img = pygame.transform.smoothscale(trunk_base_orig, (trunk_size, trunk_size))
        self.trunk_img = pygame.transform.smoothscale(trunk_orig, (trunk_size, trunk_size))
        self.leaves_img = pygame.transform.smoothscale(leaves_orig, (leaves_size, leaves_size))

        # Trees - positioned relative to minigame area with random heights
        self.tree_spacing = 150
        self.num_trees = 10
        self.trees = []

        # Dynamic camera with zoom and smooth follow
        self.camera = dynamic_camera.DynamicCamera()
        self.camera.idle_zoom = 1.0
        self.camera.action_zoom = 1.15  #Slight zoom during swing
        self.camera.follow_speed = 4.0  # Smooth follow
        self.camera.zoom_speed = 2.0
        self.world_width = self.tree_spacing * (self.num_trees + 2)

        # Position trees in world space with random trunk segment counts
        for i in range(self.num_trees):
            tree_x = 150 + i * self.tree_spacing
            tree_trunk_segments = random.randint(1, 3)  # Less extreme heights (1-3 segments)
            self.trees.append({
                'x': tree_x,
                'trunk_segments': tree_trunk_segments
            })

        # Player state - animated hero character
        self.current_tree = 0
        self.player_world_x = self.trees[0]['x']  # Player position in world space
        self.rope_length = 200  # Fixed distance below leaves
        self.player_y = 200  # Will be recalculated in first update

        # Load animated hero with swing animation
        self.hero_sprite = hero.create_game_hero(0, 0, "swing")
        self.hero_sprite.scale = 0.25  # Scale to ~128px
        self.hero_offset_x = -60  # Offset left to center
        self.hero_offset_y = -60  # Offset up to center vertically

        # Swinging animation with phases
        self.swing_state = "idle"  # idle, charge, midair, catch
        self.swing_progress = 0
        self.swing_start_x = 0
        self.swing_target_x = 0
        self.swing_start_y = 200
        self.swing_target_y = 200
        self.charge_timer = 0  # Time spent in charge animation
        self.catch_timer = 0  # Time spent in catch animation
        self.last_rep_count = 0  # Track previous rep count to detect new reps

    def reset_reps(self):
        """Full reset - return to starting position."""
        self.current_tree = 0
        self.player_world_x = self.trees[0]['x']
        self.camera.x = 0
        self.camera.target_x = 0
        self.swing_state = "idle"
        self.charge_timer = 0
        self.catch_timer = 0
        self.last_rep_count = 0

    def reset_reps_only(self):
        """Reset only the rep tracking, keep player progress intact."""
        # Reset rep tracking so new exercise can detect reps
        self.last_rep_count = 0

    def update(self, dt, rep_progress, rep_count):
        """Update minigame state."""
        # Generate more trees if needed (infinite scrolling)
        if self.current_tree >= len(self.trees) - 5:
            # Add 10 more trees
            for i in range(10):
                new_index = len(self.trees)
                tree_x = 150 + new_index * self.tree_spacing
                tree_trunk_segments = random.randint(1, 3)
                self.trees.append({
                    'x': tree_x,
                    'trunk_segments': tree_trunk_segments
                })
            self.world_width = self.tree_spacing * (len(self.trees) + 2)

        # Check if we should start a new swing (detect NEW rep, not absolute count)
        if rep_count > self.last_rep_count:
            if self.swing_state == "idle":
                # Start charge phase
                self.swing_state = "charge"
                self.charge_timer = 0
                self.swing_progress = 0
                self.swing_start_x = self.player_world_x
                self.swing_start_y = self.player_y
                self.current_tree += 1
                self.swing_target_x = self.trees[self.current_tree]['x']
                self.swing_target_y = self._calculate_player_y(self.current_tree)
                self.hero_sprite.set_animation("charge", reset=True)
            self.last_rep_count = rep_count

        # Update swing state machine
        if self.swing_state == "charge":
            # Charge phase: swing back animation (23 frames @ 30fps = 0.77 seconds)
            self.charge_timer += dt
            if self.charge_timer >= 0.77:  # Animation duration
                # Move to midair phase and start physical swing
                self.swing_state = "midair"
                self.swing_progress = 0
                self.hero_sprite.set_animation("midair", reset=True)

        elif self.swing_state == "midair":
            # Midair phase: physical swing happens here (slower for animation)
            self.swing_progress += dt * 1.2  # Slower swing speed (was 2.5)

            if self.swing_progress >= 1.0:
                # Start catch phase
                self.swing_state = "catch"
                self.catch_timer = 0
                self.player_world_x = self.swing_target_x
                self.player_y = self.swing_target_y
                self.hero_sprite.set_animation("catch", reset=True)
            else:
                # Smooth swing with arc
                t = animations.ease_out_cubic(self.swing_progress)
                self.player_world_x = self.swing_start_x + (self.swing_target_x - self.swing_start_x) * t
                self.player_y = self.swing_start_y + (self.swing_target_y - self.swing_start_y) * t

                # Add arc to the swing (pendulum motion)
                arc_height = 40 * math.sin(self.swing_progress * math.pi)
                self.player_y += arc_height

        elif self.swing_state == "catch":
            # Catch phase: landing animation (45 frames @ 30fps = 1.5 seconds)
            self.catch_timer += dt
            if self.catch_timer >= 1.5:  # Animation duration
                # Return to idle
                self.swing_state = "idle"
                self.hero_sprite.set_animation("idle", reset=True)

        else:  # idle state
            # Always calculate correct Y position when idle
            self.player_y = self._calculate_player_y(self.current_tree)

        # Update camera to follow player with zoom
        target_camera_x = self.player_world_x - self.rect.width // 3  # Player offset from left
        self.camera.set_target(target_camera_x, 0)
        self.camera.set_moving(self.swing_state in ["charge", "midair", "catch"])
        self.camera.update(dt)

        # Clamp camera position
        self.camera.x = max(0, min(self.camera.x, self.world_width - self.rect.width))

        # Update hero animation
        self.hero_sprite.update(dt)

    def _calculate_player_y(self, tree_index):
        """Calculate player Y position based on tree leaf height."""
        tree = self.trees[tree_index]
        # Calculate where the leaves bottom is for this tree
        ground_y = self.rect.height - 50
        base_h = self.trunk_base_img.get_height()
        trunk_h = self.trunk_img.get_height()
        leaves_h = self.leaves_img.get_height()

        # Leaf bottom position: ground - base - trunks - leaves + overlap
        trunk_top_y = ground_y - base_h - (tree['trunk_segments'] * trunk_h)
        leaves_bottom_y = trunk_top_y - leaves_h + 80  # 80px overlap

        # Player hangs at fixed distance below leaves bottom
        return leaves_bottom_y + self.rope_length

    def draw(self):
        """Draw the jungle minigame."""
        self.screen.set_clip(self.rect)

        # Draw gradient green background (light to dark from top to bottom)
        self._draw_gradient_background()

        # Ground
        ground_y = self.rect.y + self.rect.height - 50
        pygame.draw.rect(self.screen, (40, 80, 40),
                        (self.rect.x, ground_y, self.rect.width, 50))

        # Get camera offset and zoom
        camera_x, _ = self.camera.get_offset()
        zoom = self.camera.get_zoom()

        # Draw trees with camera offset and zoom
        for i, tree_data in enumerate(self.trees):
            tree_world_x = tree_data['x']
            # Convert world position to screen position with zoom
            screen_offset_x = (tree_world_x - camera_x) * zoom
            tree_screen_x = self.rect.x + int(screen_offset_x)

            # Skip if off-screen
            if tree_screen_x < self.rect.x - 200 or tree_screen_x > self.rect.x + self.rect.width + 200:
                continue

            self._draw_tree(tree_screen_x, tree_data['trunk_segments'], i == self.current_tree, zoom)

        # Draw animated hero with zoom
        player_screen_offset_x = (self.player_world_x - camera_x) * zoom
        player_screen_x = self.rect.x + int(player_screen_offset_x)
        player_screen_y = self.rect.y + int(self.player_y * zoom)

        # Update hero position, scale with zoom, and draw
        self.hero_sprite.x = player_screen_x + self.hero_offset_x
        self.hero_sprite.y = player_screen_y + self.hero_offset_y
        self.hero_sprite.scale = 0.25 * zoom  # Scale hero with zoom
        self.hero_sprite.draw(self.screen)

        # Progress text
        progress_text = f"Tree {self.current_tree + 1}/{len(self.trees)}"
        text_surf = theme.FONTS['body'].render(progress_text, True, theme.WHITE)
        self.screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))

        # Reset clipping
        self.screen.set_clip(None)

    def _draw_gradient_background(self):
        """Draw a gradient green background from light to dark."""
        # Light green at top, darker at bottom
        top_color = (100, 200, 120)
        bottom_color = (20, 80, 40)

        num_steps = 50
        for i in range(num_steps):
            t = i / num_steps
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)

            y = self.rect.y + int(i * self.rect.height / num_steps)
            height = int(self.rect.height / num_steps) + 1
            pygame.draw.rect(self.screen, (r, g, b), (self.rect.x, y, self.rect.width, height))

    def _draw_tree(self, screen_x, trunk_segments, is_current, zoom=1.0):
        """Draw a tree using sprites: trunk_base + stacked trunks + leaves."""
        ground_y = self.rect.y + int((self.rect.height - 30) * zoom)

        # Scale sprites with zoom
        if zoom != 1.0:
            trunk_base = pygame.transform.smoothscale(self.trunk_base_img,
                (int(self.trunk_base_img.get_width() * zoom), int(self.trunk_base_img.get_height() * zoom)))
            trunk = pygame.transform.smoothscale(self.trunk_img,
                (int(self.trunk_img.get_width() * zoom), int(self.trunk_img.get_height() * zoom)))
            leaves = pygame.transform.smoothscale(self.leaves_img,
                (int(self.leaves_img.get_width() * zoom), int(self.leaves_img.get_height() * zoom)))
        else:
            trunk_base = self.trunk_base_img
            trunk = self.trunk_img
            leaves = self.leaves_img

        # Draw trunk base at ground level (no gap)
        base_w = trunk_base.get_width()
        base_h = trunk_base.get_height()
        base_x = screen_x - base_w // 2
        base_y = ground_y  # Start at ground, image extends upward
        self.screen.blit(trunk_base, (base_x, base_y - base_h))

        # Stack trunk segments on top of base (no gaps)
        trunk_w = trunk.get_width()
        trunk_h = trunk.get_height()
        trunk_x = screen_x - trunk_w // 2

        trunk_top_y = base_y - base_h  # Start right at top of base
        for segment in range(trunk_segments):
            trunk_y = trunk_top_y - segment * trunk_h
            self.screen.blit(trunk, (trunk_x, trunk_y - trunk_h))

        # Draw leaves on top with significant overlap over the trunk
        leaves_w = leaves.get_width()
        leaves_h = leaves.get_height()
        leaves_x = screen_x - leaves_w // 2
        leaves_top_y = trunk_top_y - trunk_segments * trunk_h
        # Overlap more of the top trunk for natural tree appearance
        leaves_y = leaves_top_y - leaves_h + int(80 * zoom)  # More overlap
        self.screen.blit(leaves, (leaves_x, leaves_y))