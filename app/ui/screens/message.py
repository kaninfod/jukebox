import logging
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from PIL import Image

logger = logging.getLogger(__name__)

class MessageScreen(Screen):
    # event_type = "show_message_screen"
    # name = "Message Screen"

    """
    Generic message screen for displaying a title, icon, and message.
    Context keys:
        - title: str (title text)
        - icon_name: str (icon key from ICON_DEFINITIONS)
        - message: str or list of str (message lines)
        - color: str (optional, text color)
    """
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.context = {}
        self.name = "Message Screen"

    @staticmethod
    def show(context=None):
        """Emit an event to show the home screen via the event bus."""
        from app.core import event_bus, EventType, Event
        event_bus.emit(Event(
            type=EventType.SHOW_MESSAGE,
            payload=context
        ))

        # from app.core import event_bus, EventFactory
        # event_bus.emit(EventFactory.show_home(payload=context))
        logger.info(f"EventBus: Emitted 'show_home' event from HomeScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        theme = self.theme
        # Draw background, allow override from context
        bg_color = self.context.get("background", theme.colors["background"])
        draw_context.rectangle([0, 0, self.width, self.height], fill=bg_color)
        # Title
        title = self.context.get("title", "Message")
        title_font = theme.fonts["title"]
        title_bbox = draw_context.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, theme.layout["title_y"]), title, fill=theme.colors["text"], font=title_font)
        # Icon
        icon_name = self.context.get("icon_name", None)
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_icon(draw_context, icon_x, icon_y, icon_size, image=image, icon_name=icon_name)
        # Message
        message = self.context.get("message", "")
        if isinstance(message, str):
            message_lines = message.split('\n')
        else:
            message_lines = list(message)
        info_font = theme.fonts["info"]
        color = self.context.get("color", theme.colors["text"])
        message_y = icon_y + icon_size + 30
        line_height = theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=color, font=info_font)
        
        logger.debug(f"MessageScreen drawn with title '{title}' and message lines: {message_lines}")

    def _draw_icon(self, draw, x, y, size, image=None, icon_name=None):
        from app.config import config
        icon_path = icon_name
        icon_img = None
        if icon_path:
            #from app.ui.manager import ScreenManager
            try:
                icon_img = Image.open(icon_path).convert("RGBA")
                #icon_img = ScreenManager.get_icon_png(icon_path)
            except Exception as e:
                logger.error(f"Failed to load icon PNG: {e}")
        if icon_img:
            icon_img = icon_img.resize((size, size), resample=Image.LANCZOS)
            if image is not None:
                image.paste(icon_img, (x, y), icon_img)
            else:
                draw.im.paste(icon_img, (x, y), icon_img)
                logger.warning(f"Custom draw wrapper used for icon '{icon_name}'")
        else:
            draw.ellipse([x, y, x + size, y + size], fill="gray", outline="black", width=2)
            draw.text((x + size // 2 - 8, y + size // 2 - 8), "?", fill="white")
