import pygame
import random
import math

class PaintSplatter:
    """Creates paint splatter effects for Persona-style UI"""
    def __init__(self, x, y, color, size=50):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.splatters = []
        self._generate_splatters()

    def _generate_splatters(self):
        """Generate random splatter shapes"""
        num_blobs = random.randint(5, 10)
        for _ in range(num_blobs):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, self.size)
            blob_size = random.randint(5, 20)
            blob_x = self.x + math.cos(angle) * dist
            blob_y = self.y + math.sin(angle) * dist
            self.splatters.append((blob_x, blob_y, blob_size))

    def draw(self, surface):
        """Draw the paint splatter effect"""
        for blob_x, blob_y, blob_size in self.splatters:
            pygame.draw.circle(surface, self.color, (int(blob_x), int(blob_y)), blob_size)


class BrushStroke:
    """Creates brush stroke effects"""
    def __init__(self, start_pos, end_pos, color, thickness=10):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.thickness = thickness

    def draw(self, surface):
        """Draw a rough brush stroke"""
        # Draw main line
        pygame.draw.line(surface, self.color, self.start_pos, self.end_pos, self.thickness)

        # Add some rough edges
        steps = 5
        for i in range(steps):
            t = i / steps
            x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
            y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
            offset = random.randint(-3, 3)
            pygame.draw.circle(surface, self.color, (int(x + offset), int(y + offset)),
                             self.thickness // 2 + random.randint(0, 2))


class GrungeTexture:
    """Creates a grunge texture overlay"""
    def __init__(self, width, height, color, alpha=50):
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.color = (*color, alpha)
        self._generate_texture()

    def _generate_texture(self):
        """Generate random grunge texture"""
        width, height = self.surface.get_size()
        for _ in range(200):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 4)
            alpha = random.randint(20, 100)
            color = (*self.color[:3], alpha)
            pygame.draw.circle(self.surface, color, (x, y), size)

    def draw(self, surface):
        """Draw the texture overlay"""
        surface.blit(self.surface, (0, 0))


def draw_slanted_text(surface, font, text, color, center_pos, angle=15):
    """Draw text at a slant angle (like Persona menus)"""
    # Render text
    text_surf = font.render(text, True, color)

    # Create a larger surface for rotation
    w, h = text_surf.get_size()
    rotated_size = int(math.sqrt(w**2 + h**2) * 1.5)
    temp_surf = pygame.Surface((rotated_size, rotated_size), pygame.SRCALPHA)

    # Blit text to center of temp surface
    temp_rect = text_surf.get_rect(center=(rotated_size // 2, rotated_size // 2))
    temp_surf.blit(text_surf, temp_rect)

    # Rotate
    rotated = pygame.transform.rotate(temp_surf, angle)
    rotated_rect = rotated.get_rect(center=center_pos)

    surface.blit(rotated, rotated_rect)
    return rotated_rect


def draw_strikethrough(surface, text_rect, color, thickness=4):
    """Draw a strikethrough effect on text (Persona style)"""
    start_x = text_rect.left - 10
    end_x = text_rect.right + 10
    y = text_rect.centery
    pygame.draw.line(surface, color, (start_x, y), (end_x, y), thickness)
