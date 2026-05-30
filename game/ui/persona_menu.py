import pygame
from game.ui import theme, animations

class PersonaMenu:
    def __init__(self, items, x, y, width=400, item_height=70):
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height

        self.selected_idx = 0
        self.selector_y = y
        self.target_y = y
        self.angle_cut = 20
        self.offset_left = 40
        self.pulse_time = 0

    def update(self, dt):
        # Smoothly slide selector
        self.target_y = self.y + (self.selected_idx * self.item_height)
        self.selector_y += (self.target_y - self.selector_y) * 15 * dt

        self.pulse_time += dt

    def draw(self, surface):
        for i, item in enumerate(self.items):
            item_y = self.y + (i * self.item_height)
            is_selected = (i == self.selected_idx)

            # Draw selector parallelogram if selected
            if is_selected:
                self._draw_selector(surface)

            # Draw text
            color = theme.BLACK if is_selected else theme.TEXT
            text_surf = theme.FONTS['menu'].render(item, True, color)
            text_rect = text_surf.get_rect(midleft=(self.x + 20, item_y + self.item_height//2))
            surface.blit(text_surf, text_rect)

    def _draw_selector(self, surface):
        glow = animations.oscillate(self.pulse_time, 20, 1.5, 235)
        color = (glow, glow, glow)

        # Parallelogram corners
        points = [
            (self.x - self.offset_left, self.selector_y),
            (self.x + self.width,       self.selector_y + self.angle_cut),
            (self.x + self.width - self.angle_cut, self.selector_y + self.item_height),
            (self.x - self.offset_left + self.angle_cut, self.selector_y + self.item_height)
        ]

        pygame.draw.polygon(surface, theme.ACCENT, points)
        pygame.draw.polygon(surface, color, points, 3)

    def next(self):
        self.selected_idx = (self.selected_idx + 1) % len(self.items)

    def prev(self):
        self.selected_idx = (self.selected_idx - 1) % len(self.items)
