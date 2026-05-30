import pygame
from game.ui import theme, animations

class CompletionScreen:
    def __init__(self, screen, score):
        self.screen = screen
        self.score = score
        self.options = ["RESTART", "MISSIONS", "MAIN MENU"]
        self.selected_idx = 0
        self.alpha = 0
        self.anim_t = 0
        self.finished = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_idx = (self.selected_idx - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_idx = (self.selected_idx + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self.finished = True
                return self.options[self.selected_idx]
        return None

    def update(self, dt):
        self.anim_t = min(1.0, self.anim_t + dt)
        self.alpha = min(255, self.alpha + 500 * dt)

    def draw_parallelogram(self, surface, rect, color, alpha=255, angle=10):
        width, height = rect.width, rect.height
        x, y = rect.x, rect.y
        offset = 15 # Fixed offset for simplicity

        points = [
            (x + offset, y),
            (x + width + offset, y),
            (x + width, y + height),
            (x, y + height)
        ]

        s = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*color, alpha), points)
        surface.blit(s, (0, 0))

    def draw(self):
        # Semi-transparent dark overlay
        overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 200))
        self.screen.blit(overlay, (0, 0))

        # Big "MISSION COMPLETE"
        title_txt = theme.FONTS['title'].render("MISSION COMPLETE", True, theme.WHITE)
        title_rect = title_txt.get_rect(center=(theme.WIDTH // 2, 150))

        # Slanted background for title
        bg_rect = pygame.Rect(title_rect.x - 50, title_rect.y - 10, title_rect.width + 100, title_rect.height + 20)
        self.draw_parallelogram(self.screen, bg_rect, theme.ACCENT, 180, 15)
        self.screen.blit(title_txt, title_rect)

        # Final Score
        score_txt = theme.FONTS['menu'].render(f"FINAL SCORE: {self.score:05d}", True, theme.ACCENT)
        self.screen.blit(score_txt, score_txt.get_rect(center=(theme.WIDTH // 2, 250)))

        # Options
        start_y = 350
        for i, opt in enumerate(self.options):
            is_sel = i == self.selected_idx
            color = theme.WHITE if is_sel else theme.GRAY
            opt_txt = theme.FONTS['menu'].render(opt, True, color)

            if is_sel:
                # Background for selected
                sel_bg = pygame.Rect(theme.WIDTH // 2 - 150, start_y + i * 80 - 5, 300, 60)
                self.draw_parallelogram(self.screen, sel_bg, theme.ACCENT_LOW, 200, 10)

            self.screen.blit(opt_txt, opt_txt.get_rect(center=(theme.WIDTH // 2, start_y + i * 80 + 25)))
