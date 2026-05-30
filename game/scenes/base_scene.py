class BaseScene:
    def __init__(self, screen):
        self.screen = screen
        self.next_scene = None

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass

    def on_enter(self, prev_scene_data=None):
        pass

    def on_exit(self):
        return None
