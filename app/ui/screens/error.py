from app.ui.theme import UITheme
from app.ui.screens.base import Screen

class ErrorScreen(Screen):
    def __init__(self, theme, width=480, height=320, error_message=""):
        super().__init__(width, height)
        self.theme = theme
        self.name = "Error"
        self.error_message = error_message

    def set_error(self, error_message):
        self.error_message = error_message
        self.dirty = True

    def draw(self, draw_context, fonts, context=None, image=None):
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["error"])
        error_font = self.theme.fonts["title"]
        text_bbox = draw_context.textbbox((0, 0), self.error_message, font=error_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (self.width - text_width) // 2
        text_y = (self.height - text_height) // 2
        draw_context.text((text_x, text_y), self.error_message, fill=self.theme.colors["background"], font=error_font)
