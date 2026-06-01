import pygame
from game.ui import theme, animations

class LevelCard:
    def __init__(self, group_data, target_x, y, width=500, height=120):
        self.data = group_data
        self.target_x = target_x
        self.start_x = theme.WIDTH
        self.x = self.start_x
        self.y = y
        self.width = width
        self.height = height
        self.alpha = 0
        self.anim_t = 0.0

        # Pre-render texts
        raw_icon = theme.FONTS['emoji'].render(self.data['icon'], True, theme.WHITE)
        self.icon_surf = pygame.transform.scale(raw_icon, (48, 48))

        self.name_surf = theme.FONTS['menu'].render(self.data['name'].upper(), True, theme.WHITE)
        self.sub_surf = theme.FONTS['body'].render(self.data['subtitle'], True, theme.GRAY)

        ex_names = [e.replace('.npz', '').replace('_', ' ').title() for e in self.data['exercises']]
        self.ex_list_surf = theme.FONTS['small'].render(" · ".join(ex_names), True, theme.ACCENT)

    def update(self, dt, delay_timer):
        if delay_timer <= 0:
            self.anim_t = min(1.0, self.anim_t + 1.5 * dt)
            e = animations.ease_out_expo(self.anim_t)
            self.x = animations.lerp(self.start_x, self.target_x, e)
            self.alpha = min(255, self.alpha + 500 * dt)

        # Determine current hit box for hover/click
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface, is_selected, pulse_time):
        render_x = self.x

        # 1. Shadow / Background
        bg_rect = pygame.Rect(render_x, self.y, self.width, self.height)

        # Darker background for unselected
        if is_selected:
            pygame.draw.rect(surface, (15, 15, 20), bg_rect, border_radius=8)
        else:
            pygame.draw.rect(surface, (10, 10, 15), bg_rect, border_radius=8)
            pygame.draw.rect(surface, theme.ACCENT_LOW, bg_rect, 2, border_radius=8)

        # 2. Selected Highlight (Bold Red Parallelogram)
        if is_selected:
            glow = min(255, max(0, int(animations.oscillate(pulse_time, 50, 2.5, 255))))
            glow_color = (glow, glow // 4, glow // 4)  # Reddish glow

            points = [
                (int(render_x - 40), int(self.y - 5)),
                (int(render_x + self.width + 30), int(self.y + 15)),
                (int(render_x + self.width - 15), int(self.y + self.height + 5)),
                (int(render_x - 15), int(self.y + self.height - 5))
            ]

            # Shadow for depth
            shadow_points = [(int(p[0] + 3), int(p[1] + 3)) for p in points]
            pygame.draw.polygon(surface, theme.BLACK, shadow_points)

            # Main red highlight
            pygame.draw.polygon(surface, theme.ACCENT, points, 5)

            # Glowing border
            pygame.draw.polygon(surface, glow_color, points, 2)

            # Subtle red fill
            s = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*theme.ACCENT, 30), points)
            surface.blit(s, (0,0))

            # Corner accent (white triangle)
            corner_points = [
                points[0],
                (points[0][0] + 20, points[0][1]),
                (points[0][0], points[0][1] + 20)
            ]
            pygame.draw.polygon(surface, theme.WHITE, corner_points)

        # 3. Content with bolder styling
        surface.blit(self.icon_surf, (render_x + 20, self.y + 20))

        # Name with color based on selection
        name_color = theme.WHITE if is_selected else theme.GRAY
        name_surf = theme.FONTS['menu'].render(self.data['name'].upper(), True, name_color)
        surface.blit(name_surf, (render_x + 100, self.y + 20))

        # Subtitle
        sub_color = theme.CYAN if is_selected else theme.GRAY
        sub_surf = theme.FONTS['body'].render(self.data['subtitle'], True, sub_color)
        surface.blit(sub_surf, (render_x + 100, self.y + 60))

        # Exercise list
        ex_color = theme.ACCENT if is_selected else theme.ACCENT_LOW
        ex_names = [e.replace('.npz', '').replace('_', ' ').title() for e in self.data['exercises']]
        ex_list_surf = theme.FONTS['small'].render(" · ".join(ex_names), True, ex_color)
        surface.blit(ex_list_surf, (render_x + 100, self.y + 90))

class LevelCardMenu:
    def __init__(self, groups, target_x, y):
        self.cards = []
        for i, g in enumerate(groups):
            card_y = y + (i * 150)
            # Add horizontal stagger (Persona style diagonal)
            stagger_x = target_x + (i * 40)
            self.cards.append(LevelCard(g, stagger_x, card_y))

        self.selected_idx = 0
        self.pulse_time = 0
        self.entry_timer = 0.0
        self.mouse_active = True

    def update(self, dt):
        # Handle Mouse Hover
        if self.mouse_active:
            mouse_pos = pygame.mouse.get_pos()
            for i, card in enumerate(self.cards):
                card_rect = pygame.Rect(card.x, card.y, card.width, card.height)
                if card_rect.collidepoint(mouse_pos):
                    if self.selected_idx != i:
                        self.selected_idx = i
                        from game.core.audio_manager import get_audio_manager
                        get_audio_manager().play_sfx('select')
                    break

        self.pulse_time += dt
        self.entry_timer += dt
        for i, card in enumerate(self.cards):
            # Added a base 0.2s delay for the first card to ensure it slides in
            card.update(dt, self.entry_timer - (i * 0.2 + 0.2))

        # Background elements (Persona-style shapes)
        pass

    def draw(self, surface):
        for i, card in enumerate(self.cards):
            card.draw(surface, i == self.selected_idx, self.pulse_time)

    def next(self):
        self.selected_idx = (self.selected_idx + 1) % len(self.cards)

    def prev(self):
        self.selected_idx = (self.selected_idx - 1) % len(self.cards)
        self._disable_mouse()

    def next(self):
        self.selected_idx = (self.selected_idx + 1) % len(self.cards)
        self._disable_mouse()

    def _disable_mouse(self):
        self.mouse_active = False
        pygame.mouse.set_visible(False)

    def handle_event(self, event):
        """Handle mouse and keyboard interaction logic."""
        if event.type == pygame.MOUSEMOTION:
            rel = event.rel
            if abs(rel[0]) > 2 or abs(rel[1]) > 2:
                self.mouse_active = True
                pygame.mouse.set_visible(True)

        if event.type == pygame.KEYDOWN:
            self._disable_mouse()

        if self.mouse_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for i, card in enumerate(self.cards):
                card_rect = getattr(card, 'rect', pygame.Rect(0,0,0,0))
                if card_rect.collidepoint(mouse_pos):
                    return True
        return False

    def get_selected_group(self):
        return self.cards[self.selected_idx].data
