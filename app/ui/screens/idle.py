import logging
from os import name
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from PIL import Image

logger = logging.getLogger(__name__)
class IdleScreen(Screen):

    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.event_type = "show_idle"
        self.name = "Idle Screen"


    @staticmethod
    def show(context=None):
        """Emit an event to show the home screen via the event bus."""
        from app.core import event_bus, EventType, Event
        event_bus.emit(Event(
            type=EventType.SHOW_IDLE,
            payload={}
        ))

        # from app.core import event_bus, EventFactory
        # event_bus.emit(EventFactory.show_idle())
        logger.info(f"EventBus: Emitted 'show_idle' event from IdleScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        self._draw_image(draw_context, 0, 0, 80, fonts, image=image)
        logger.info("IdleScreen drawn")

    def _draw_image(self, draw, x, y, size, fonts, image=None):
            from app.config import config
            icon_name = "klangmeister"
            icon_path = config.get_icon_path(icon_name)
            logger.debug(f"Using image '{icon_name}' for bootscreen")
            icon_img = None
            if icon_path:
                #from app.ui.manager import ScreenManager
                icon_img = Image.open(icon_path).convert("RGBA")
                #icon_img = ScreenManager.get_icon_png(icon_path)

                if icon_img:
                    image.paste(icon_img, (x, y), icon_img)                            

            