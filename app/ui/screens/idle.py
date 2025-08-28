import logging
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from PIL import ImageDraw

logger = logging.getLogger(__name__)
class IdleScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "Idle Screen"

    @staticmethod
    def show():
        """Emit an event to show the idle screen via the event bus."""
        from app.ui.event_bus import ui_event_bus, UIEvent
        ui_event_bus.emit(UIEvent(type="show_idle"))
        logger.info("UIEventBus: Emitted show_idle event from IdleScreen.show()")


    def draw(self, draw_context, fonts, context=None, image=None):
        self._draw_image(draw_context, 0, 0, 80, fonts, image=image)
        logger.info("IdleScreen drawn")

    def _draw_image(self, draw, x, y, size, fonts, image=None):
            from app.config import ICON_DEFINITIONS
            icon_name = "klangmeister"
            icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
            logger.debug(f"Using image '{icon_name}' for bootscreen")
            icon_img = None
            if icon_def:
                from app.ui.manager import ScreenManager
                icon_img = ScreenManager.get_icon_png(icon_def["path"])

                if icon_img:
                    image.paste(icon_img, (x, y), icon_img)                            

            