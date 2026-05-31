import pygame
import random
from game.ui import theme, animations, paint_effects

class PersonaMenu:
    def __init__(self, items, x, y, width=500, item_height=90):
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height

        self.selected_idx = 0
        self.selector_y = y
        self.target_y = y
        self.angle_cut = 25
        self.offset_left = 60
        self.pulse_time = 0

        # Animated splatter that follows selection
        self.splatter_y = y
        self.splatter_target_y = y
        # Create multiple splatters for more dramatic effect
        self.active_splatters = []

    def update(self, dt):
        # Smoothly slide selector with more snap
        self.target_y = self.y + (self.selected_idx * self.item_height)
        self.selector_y += (self.target_y - self.selector_y) * 20 * dt

        # Animate splatter position to follow selection - smooth tracking
        self.splatter_target_y = self.target_y + self.item_height // 2
        self.splatter_y += (self.splatter_target_y - self.splatter_y) * 18 * dt

        # Regenerate splatters at a moderate rate (~10 times per second)
        if random.random() < dt * 10:
            self.active_splatters = [
                paint_effects.PaintSplatter(self.x - 120, self.splatter_y, theme.SPLATTER_RED, size=50),
                paint_effects.PaintSplatter(self.x + self.width + 20, self.splatter_y + 10, theme.SPLATTER_CYAN, size=35),
            ]

        self.pulse_time += dt

    def draw(self, surface):
        # Draw animated paint splatters that follow selection
        for splatter in self.active_splatters:
            splatter.draw(surface)

        for i, item in enumerate(self.items):
            item_y = self.y + (i * self.item_height)
            is_selected = (i == self.selected_idx)

            # Draw selector parallelogram if selected
            if is_selected:
                self._draw_selector(surface)

            # Draw text with bolder styling
            if is_selected:
                # Selected item - white text on red background
                text_surf = theme.FONTS['menu'].render(item, True, theme.WHITE)
                text_rect = text_surf.get_rect(midleft=(self.x + 30, item_y + self.item_height//2))

                # Add subtle glow effect
                glow_surf = theme.FONTS['menu'].render(item, True, theme.ACCENT)
                glow_rect = text_rect.copy()
                glow_rect.x -= 2
                glow_rect.y -= 2
                surface.blit(glow_surf, glow_rect)
            else:
                # Unselected - gray text with slight opacity feel
                color = theme.GRAY
                text_surf = theme.FONTS['menu'].render(item, True, color)
                text_rect = text_surf.get_rect(midleft=(self.x + 30, item_y + self.item_height//2))

            surface.blit(text_surf, text_rect)

            # Add decorative line for unselected items
            if not is_selected:
                line_y = item_y + self.item_height - 5
                pygame.draw.line(surface, theme.ACCENT_LOW,
                               (self.x - 20, line_y), (self.x + self.width - 50, line_y), 2)

    def _draw_selector(self, surface):
        # More dramatic pulsing
        glow = min(255, max(0, int(animations.oscillate(self.pulse_time, 30, 2.0, 255))))
        glow_color = (glow, glow // 4, glow // 4)  # Reddish glow

        # Main parallelogram (bold red)
        points = [
            (int(self.x - self.offset_left), int(self.selector_y)),
            (int(self.x + self.width),       int(self.selector_y + self.angle_cut)),
            (int(self.x + self.width - self.angle_cut), int(self.selector_y + self.item_height)),
            (int(self.x - self.offset_left + self.angle_cut), int(self.selector_y + self.item_height))
        ]

        # Draw shadow/depth
        shadow_points = [(int(p[0] + 4), int(p[1] + 4)) for p in points]
        pygame.draw.polygon(surface, theme.BLACK, shadow_points)

        # Draw main selector
        pygame.draw.polygon(surface, theme.ACCENT, points)

        # Draw glowing border
        pygame.draw.polygon(surface, glow_color, points, 4)

        # Add accent corner highlight
        corner_size = 15
        corner_points = [
            points[0],
            (points[0][0] + corner_size, points[0][1]),
            (points[0][0], points[0][1] + corner_size)
        ]
        pygame.draw.polygon(surface, theme.WHITE, corner_points)

    def next(self):
        self.selected_idx = (self.selected_idx + 1) % len(self.items)

    def prev(self):
        self.selected_idx = (self.selected_idx - 1) % len(self.items)
