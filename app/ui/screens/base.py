class Screen:
    def __init__(self, width=480, height=320):
        self.width = width
        self.height = height
        self.name = "Base Screen"
        self.dirty = True

    def draw(self, draw_context, fonts, jukebox_mediaplayer=None):
        pass

    def is_dirty(self, context):
        return self.dirty