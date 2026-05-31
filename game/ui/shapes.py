"""Reusable geometric shapes for UI rendering."""
import pygame
import math


def draw_parallelogram(surface, rect, color, alpha=255, angle=10):
    """
    Draws a slanted parallelogram background.

    Args:
        surface: The pygame surface to draw on
        rect: pygame.Rect defining position and size
        color: RGB tuple (r, g, b)
        alpha: Transparency (0-255). Values < 255 create a temporary surface.
        angle: Slant angle in degrees (positive = slant right)
    """
    width, height = rect.width, rect.height
    x, y = rect.x, rect.y
    offset = math.tan(math.radians(angle)) * height

    points = [
        (x + offset, y),
        (x + width + offset, y),
        (x + width, y + height),
        (x, y + height)
    ]

    if alpha < 255:
        # Create temporary surface with alpha
        temp_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        pygame.draw.polygon(temp_surface, (*color, alpha), points)
        surface.blit(temp_surface, (0, 0))
    else:
        pygame.draw.polygon(surface, color, points)


def draw_parallelogram_outline(surface, rect, color, width=2, angle=10):
    """
    Draws a slanted parallelogram outline.

    Args:
        surface: The pygame surface to draw on
        rect: pygame.Rect defining position and size
        color: RGB tuple (r, g, b)
        width: Line width in pixels
        angle: Slant angle in degrees (positive = slant right)
    """
    w, h = rect.width, rect.height
    x, y = rect.x, rect.y
    offset = math.tan(math.radians(angle)) * h

    points = [
        (x + offset, y),
        (x + w + offset, y),
        (x + w, y + h),
        (x, y + h)
    ]

    pygame.draw.polygon(surface, color, points, width)
