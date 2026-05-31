"""Dynamic camera system with smooth follow, zoom, and parallax effects."""
import pygame


class DynamicCamera:
    """Cinemachine-style camera with smooth follow and zoom."""

    def __init__(self):
        """Initialize camera with default values."""
        # Position
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0

        # Zoom
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.idle_zoom = 1.2  # Zoom level when idle
        self.action_zoom = 1.5  # Zoom level during movement

        # Smooth parameters
        self.follow_speed = 5.0  # How fast camera follows target
        self.zoom_speed = 3.0  # How fast zoom changes

        # State
        self.is_moving = False

    def set_target(self, x, y):
        """Set the camera target position."""
        self.target_x = x
        self.target_y = y

    def set_moving(self, moving):
        """Set whether the player is moving (for zoom)."""
        self.is_moving = moving
        self.target_zoom = self.action_zoom if moving else self.idle_zoom

    def update(self, dt):
        """Update camera position and zoom smoothly."""
        # Smooth follow
        self.x += (self.target_x - self.x) * self.follow_speed * dt
        self.y += (self.target_y - self.y) * self.follow_speed * dt

        # Smooth zoom
        self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed * dt

    def get_offset(self):
        """Get camera offset for rendering."""
        return self.x, self.y

    def get_zoom(self):
        """Get current zoom level."""
        return self.zoom


class ParallaxLayer:
    """A parallax background layer that moves at different speed from camera."""

    def __init__(self, surface, speed_factor):
        """
        Initialize parallax layer.

        Args:
            surface: The surface to draw
            speed_factor: How fast this layer moves relative to camera (0.0-1.0)
                         0.5 = half speed, 0.0 = static, 1.0 = same as camera
        """
        self.surface = surface
        self.speed_factor = speed_factor

    def get_offset(self, camera_x, camera_y):
        """Get the offset for this layer based on camera position."""
        return camera_x * self.speed_factor, camera_y * self.speed_factor
