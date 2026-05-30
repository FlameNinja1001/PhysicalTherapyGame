import pygame

# Colors
BACKGROUND = (10, 15, 25)
ACCENT     = (0, 230, 180)  # Cyan/Teal
ACCENT_LOW = (0, 100, 80)
TEXT       = (240, 245, 255)
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
GRAY       = (100, 105, 115)
RED        = (230, 50, 70)

# Fonts (will be initialized in theme.init())
FONTS = {
    'title': None,
    'menu': None,
    'body': None,
    'small': None
}

def init():
    # Use SysFont for simplicity or load specific .ttf files if available
    # Try to find a font that supports emojis if possible
    main_font = "Arial"
    emoji_font = "Segoe UI Emoji,Apple Color Emoji,Noto Color Emoji,Symbola,DejaVu Sans"

    FONTS['title'] = pygame.font.SysFont(main_font, 72, bold=True)
    FONTS['menu']  = pygame.font.SysFont(main_font, 42, bold=True)
    FONTS['emoji'] = pygame.font.SysFont(emoji_font, 18)
    FONTS['body']  = pygame.font.SysFont(main_font, 28)
    FONTS['small'] = pygame.font.SysFont(main_font, 18)

# Layout
WIDTH = 1280
HEIGHT = 720
