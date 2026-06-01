"""Centralized scene navigation to avoid circular imports."""


class SceneNavigator:
    """Factory for creating scenes, avoiding circular imports."""

    @staticmethod
    def create_main_menu(screen, menu_hero=None):
        from game.scenes.main_menu_scene import MainMenuScene
        return MainMenuScene(screen, menu_hero)

    @staticmethod
    def create_level_select(screen, menu_hero=None):
        from game.scenes.level_select_scene import LevelSelectScene
        return LevelSelectScene(screen, menu_hero)

    @staticmethod
    def create_how_to_play(screen, menu_hero=None):
        from game.scenes.how_to_play_scene import HowToPlayScene
        return HowToPlayScene(screen, menu_hero)

    @staticmethod
    def create_game(screen, template_paths=None):
        from game.scenes.game_scene import GameScene
        return GameScene(screen, template_paths)
