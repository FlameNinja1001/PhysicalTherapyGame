import pygame
import math
from game.ui import theme, animations, shapes

class CompletionScreen:
    def __init__(self, screen, score):
        self.screen = screen
        self.score = score
        self.options = ["MISSIONS", "MAIN MENU"]
        self.selected_idx = 0
        self.finished = False

        # Animation state
        self.anim_t = 0
        self.overlay_alpha = 0

        # PERSONA 5 STYLE: Left-side tilted title slides in
        self.title_x = animations.Tween(-800, 100, 0.9, animations.ease_out_expo)
        self.title_rotation = -10  # Tilted like P5

        # Diagonal red strips - slide from different directions
        self.strip1_x = animations.Tween(-theme.WIDTH, 0, 0.8, animations.ease_out_expo)
        self.strip2_x = animations.Tween(theme.WIDTH * 2, theme.WIDTH, 1.0, animations.ease_out_expo)

        # Score with starburst - zooms in
        self.score_scale = animations.Tween(0.0, 1.0, 1.1, animations.ease_out_expo)
        self.starburst_rotation = 0

        # Menu slides from right
        self.menu_x = animations.Tween(theme.WIDTH + 400, theme.WIDTH - 300, 1.2, animations.ease_out_expo)

        # Small accent parallelograms - scattered decorations
        self.accent1 = animations.Tween(-200, 80, 0.7, animations.ease_out_expo)
        self.accent2 = animations.Tween(theme.WIDTH + 150, theme.WIDTH - 180, 0.9, animations.ease_out_expo)
        self.accent3 = animations.Tween(-180, 120, 1.1, animations.ease_out_expo)

        # Pulse animation for selection
        self.pulse_time = 0
        self.mouse_active = True

    def handle_event(self, event):
        # Handle Mouse Motion
        if event.type == pygame.MOUSEMOTION:
            rel = event.rel
            if abs(rel[0]) > 2 or abs(rel[1]) > 2:
                self.mouse_active = True
                pygame.mouse.set_visible(True)

        # Handle Mouse Events
        if self.mouse_active:
            mouse_pos = pygame.mouse.get_pos()
            base_x = int(self.menu_x.value)
            start_y = 400

            for i in range(len(self.options)):
                opt_y = start_y + i * 85
                # Simplified click/hover area
                menu_rect = pygame.Rect(base_x - 100, opt_y, 400, 70)
                if menu_rect.collidepoint(mouse_pos):
                    if self.selected_idx != i:
                        self.selected_idx = i
                        from game.core.audio_manager import get_audio_manager
                        get_audio_manager().play_sfx('select')

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.finished = True
                        return self.options[i]

        if event.type == pygame.KEYDOWN:
            # Key priority: disable mouse
            self.mouse_active = False
            pygame.mouse.set_visible(False)

            if event.key == pygame.K_UP:
                self.selected_idx = (self.selected_idx - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_idx = (self.selected_idx + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self.finished = True
                return self.options[self.selected_idx]
        return None

    def update(self, dt):
        self.anim_t += dt
        self.pulse_time += dt

        # Fade in overlay
        self.overlay_alpha = min(230, self.overlay_alpha + 400 * dt)

        # Update all tweens
        self.title_x.update(dt)
        self.strip1_x.update(dt)
        self.strip2_x.update(dt)
        self.score_scale.update(dt)
        self.menu_x.update(dt)
        self.accent1.update(dt)
        self.accent2.update(dt)
        self.accent3.update(dt)

        # Rotate starburst
        self.starburst_rotation += 20 * dt

    def draw(self):
        sw, sh = self.screen.get_size()

        # Semi-transparent dark overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, int(self.overlay_alpha)))
        self.screen.blit(overlay, (0, 0))

        # Diagonal red strips (Persona 5 style)
        self._draw_diagonal_strips()

        # Small accent parallelograms
        self._draw_accent_parallelograms()

        # Big tilted "MISSION COMPLETE" on LEFT
        self._draw_tilted_title()

        # Menu items on right side
        self._draw_menu_items()

    def _draw_diagonal_strips(self):
        """Draw diagonal red strips like Persona 5."""
        sw, sh = self.screen.get_size()

        # Strip 1 - upper diagonal
        if self.strip1_x.value > -sw:
            strip1_y = 120
            strip_width = 1200
            strip_height = 180

            # Create parallelogram for diagonal strip
            x_offset = int(self.strip1_x.value)
            points = [
                (x_offset - 100, strip1_y),
                (x_offset + strip_width, strip1_y - 80),
                (x_offset + strip_width + 100, strip1_y + strip_height - 80),
                (x_offset, strip1_y + strip_height)
            ]

            pygame.draw.polygon(self.screen, theme.ACCENT, points)
            pygame.draw.polygon(self.screen, theme.WHITE, points, 4)

        # Strip 2 - lower diagonal (opposite direction)
        if self.strip2_x.value < sw * 2:
            strip2_y = sh - 280
            strip_width = 900
            strip_height = 140

            x_offset = int(self.strip2_x.value)
            points = [
                (x_offset + 100, strip2_y),
                (x_offset - strip_width, strip2_y + 70),
                (x_offset - strip_width - 100, strip2_y + strip_height + 70),
                (x_offset, strip2_y + strip_height)
            ]

            pygame.draw.polygon(self.screen, theme.ACCENT, points)
            pygame.draw.polygon(self.screen, theme.WHITE, points, 3)

    def _draw_accent_parallelograms(self):
        """Small decorative parallelograms scattered around."""
        # Small accent 1 - top left corner
        if self.accent1.value > -150:
            rect = pygame.Rect(int(self.accent1.value), 40, 100, 60)
            shapes.draw_parallelogram_outline(self.screen, rect, theme.ACCENT, 2, 15)

        # Small accent 2 - top right
        if self.accent2.value < theme.WIDTH + 100:
            rect = pygame.Rect(int(self.accent2.value), 70, 120, 50)
            shapes.draw_parallelogram_outline(self.screen, rect, theme.CYAN, 2, -20)

        # Small accent 3 - bottom left
        if self.accent3.value > -150:
            rect = pygame.Rect(int(self.accent3.value), theme.HEIGHT - 180, 90, 70)
            shapes.draw_parallelogram_outline(self.screen, rect, theme.WHITE, 1, 18)

    def _draw_tilted_title(self):
        """Draw big tilted MISSION COMPLETE on the left."""
        if self.title_x.value > -700:
            # Create huge text
            title_font = pygame.font.SysFont("Arial", 130, bold=True)
            title_text = "MISSION"
            complete_text = "COMPLETE"

            # Position on left side
            x_pos = int(self.title_x.value) - 100
            y_pos = 180

            # Draw huge shadow strips behind text for better P5 look
            sw, sh = self.screen.get_size()
            strip_y = y_pos + 50
            strip_points = [
                (x_pos - 100, strip_y),
                (x_pos + 750, strip_y - 120),
                (x_pos + 780, strip_y + 180),
                (x_pos - 70, strip_y + 300)
            ]
            pygame.draw.polygon(self.screen, (0, 0, 0, 180), strip_points)

            # Render and Rotate
            title_surf = title_font.render(title_text, True, theme.WHITE)
            complete_surf = title_font.render(complete_text, True, theme.WHITE)

            title_surf = pygame.transform.rotate(title_surf, self.title_rotation)
            complete_surf = pygame.transform.rotate(complete_surf, self.title_rotation)

            # Shadow for text
            shadow_color = (40, 0, 0)
            s_title = title_font.render(title_text, True, shadow_color)
            s_complete = title_font.render(complete_text, True, shadow_color)
            s_title = pygame.transform.rotate(s_title, self.title_rotation)
            s_complete = pygame.transform.rotate(s_complete, self.title_rotation)

            self.screen.blit(s_title, (x_pos + 12, y_pos + 12))
            self.screen.blit(s_complete, (x_pos + 32, y_pos + 152))

            self.screen.blit(title_surf, (x_pos, y_pos))
            self.screen.blit(complete_surf, (x_pos + 20, y_pos + 140))

    def _draw_menu_items(self):
        """Draw menu items on right side with tilt and staggered black parallelograms."""
        if self.menu_x.value < theme.WIDTH + 300:
            base_x = int(self.menu_x.value)
            start_y = 400

            # Draw staggered black background parallelograms FIRST for all items
            for i in range(len(self.options)):
                opt_y = start_y + i * 85
                # Stagger effect: offset every other parallelogram
                stagger_x = (i % 2) * 30
                bg_rect = pygame.Rect(base_x - 100 + stagger_x, opt_y - 10, 500, 70)
                shapes.draw_parallelogram(self.screen, bg_rect, theme.BLACK, 255, -15)

            for i, opt in enumerate(self.options):
                is_sel = i == self.selected_idx
                opt_y = start_y + i * 85

                # Create tilted menu item
                opt_font = theme.FONTS['menu']
                opt_surf = opt_font.render(opt, True, theme.WHITE if is_sel else theme.GRAY)

                # Tilt slightly
                tilt_angle = -5 if is_sel else -3
                opt_surf = pygame.transform.rotate(opt_surf, tilt_angle)

                # Selection effect
                if is_sel:
                    glow = max(0, min(255, int(animations.oscillate(self.pulse_time, 40, 2.5, 255))))
                    glow_color = (int(glow), int(glow // 4), int(glow // 4))

                    # Selection highlight
                    sel_rect = pygame.Rect(base_x - 20, opt_y - 15, 280, 65)
                    shapes.draw_parallelogram(self.screen, sel_rect, glow_color, 120, -15)
                    shapes.draw_parallelogram_outline(self.screen, sel_rect, theme.WHITE, 3, -15)

                    # Cyan triangle accent
                    tri_points = [
                        (sel_rect.x + 15, sel_rect.y + 5),
                        (sel_rect.x + 35, sel_rect.y + 5),
                        (sel_rect.x + 25, sel_rect.y + 25)
                    ]
                    pygame.draw.polygon(self.screen, theme.CYAN, tri_points)

                # Draw text
                opt_rect = opt_surf.get_rect(midleft=(base_x, opt_y + 20))

                if is_sel:
                    # Glow effect
                    glow_surf = opt_font.render(opt, True, theme.ACCENT)
                    glow_surf = pygame.transform.rotate(glow_surf, tilt_angle)
                    glow_rect = glow_surf.get_rect(midleft=(base_x - 2, opt_y + 18))
                    self.screen.blit(glow_surf, glow_rect)

                self.screen.blit(opt_surf, opt_rect)
