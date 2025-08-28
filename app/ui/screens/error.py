from app.ui.theme import UITheme
from app.ui.screens.base import Screen
import logging

logger = logging.getLogger(__name__)

class ErrorScreen(Screen):
    @staticmethod
    def show(context=None):
        """Emit an event to show the error screen via the event bus."""
        from app.ui.event_bus import ui_event_bus, UIEvent
        ui_event_bus.emit(UIEvent(type="show_error", payload=context or {}))
        
        logger.info("UIEventBus: Emitted show_error event from ErrorScreen.show()")

    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.name = "Error"
        self.error_message = ""

    def draw(self, draw_context, fonts, context=None, image=None):
        logger.debug("ErrorScreen draw started")
        try:
            if context:
                self.error_message = context.get("error_message", "Unknown error occurred")
            # Always fill background with error color
            draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["error"])
            error_font = self.theme.fonts["title"]
            # Use a contrasting color for text (e.g., white)
            text_color = self.theme.colors.get("on_error", "#FFFFFF")
            text_bbox = draw_context.textbbox((0, 0), self.error_message, font=error_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (self.width - text_width) // 2
            text_y = (self.height - text_height) // 2
            draw_context.text((text_x, text_y), self.error_message, fill=text_color, font=error_font)
            logger.info("ErrorScreen drawn with message: " + self.error_message)
        except Exception as e:
            logger.error(f"Failed to draw ErrorScreen: {e}")
            # Still fill background red if text drawing fails
            draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["error"])
            if image:
                try:
                    image.save("/tmp/error_screen_failed.png")
                    logger.info("Saved failed error screen image to /tmp/error_screen_failed.png")
                except Exception as save_e:
                    logger.error(f"Failed to save error screen image: {save_e}")
        logger.debug("ErrorScreen draw finished")
        image.save("tests/display_error.png")