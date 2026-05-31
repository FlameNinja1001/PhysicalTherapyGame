"""Centralized scene navigation to avoid circular imports."""


class SceneNavigator:
    """Factory for creating scenes, avoiding circular imports."""

    @staticmethod
    def create_main_menu(screen):
        from game.scenes.main_menu_scene import MainMenuScene
        return MainMenuScene(screen)

    @staticmethod
    def create_level_select(screen):
        from game.scenes.level_select_scene import LevelSelectScene
        return LevelSelectScene(screen)

    @staticmethod
    def create_exercise_select(screen):
        from game.scenes.exercise_select_scene import ExerciseSelectScene
        return ExerciseSelectScene(screen)

    @staticmethod
    def create_game(screen, template_paths=None):
        from game.scenes.game_scene import GameScene
        return GameScene(screen, template_paths)
