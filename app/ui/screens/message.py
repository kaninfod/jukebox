import logging, os
from app.ui.theme import UITheme 
from app.config import config
from app.ui.screens.base import Screen, RectElement, TextElement, ImageElement
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
        self.screen_theme = None
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
        logger.info(f"EventBus: Emitted 'show_home' event from HomeScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        theme = self.theme
        

        box = (0, 0, self.width, self.height)
        background_element = RectElement(*box, "white")
        background_element.draw(draw_context)

        box = (20, 30, 350, 50)
        title = self.context.get("title", "Message")
        screen_title_element = TextElement(*box, title, fonts["title"])
        screen_title_element.draw(draw_context)

        icon_name = self.context.get("icon_name", None)
        path = config.get_image_path(icon_name)
        img = self._load_album_image(path)
        box = (150, 80, 120, 120)
        album_cover_element = ImageElement(*box, img)
        album_cover_element.draw(draw_context, image)

        box = (20, 250, 350, 50)
        message = self.context.get("message", "")
        screen_message_element = TextElement(*box, message, fonts["info"])
        screen_message_element.draw(draw_context)

        return


        bg_color = theme.colors["background"]
        color = theme.colors["text"]
        icon_name = self.context.get("icon_name", None)

        if context and "theme" in context:
            theme_override = context["theme"]
            theme_dict = self.theme.get_theme(theme_override)
            if theme_dict:
                bg_color = theme_dict.get("background", bg_color)
                color = theme_dict.get("color", color)
                icon_name = theme_dict.get("icon", icon_name)

        logger.info(f"bg_color: {bg_color}, color: {color}, icon_name: {icon_name}")

        logger.info(f"MessageScreen context: {self.context} and {self.screen_theme}")
        # Draw background, allow override from context
        # bg_color = self.screen_theme.get("background", theme.colors["background"])
        draw_context.rectangle([0, 0, self.width, self.height], fill=bg_color)
        # Title
        title = self.context.get("title", "Message")
        title_font = theme.fonts["title"]
        title_bbox = draw_context.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, theme.layout["title_y"]), title, fill=theme.colors["text"], font=title_font)
        # Icon
    

        # Icon selection: context > theme > fallback
        # icon_name = self.context.get("icon_name", None)
        # logger.info(f"MessageScreen icon_name: {icon_name}")
        # if not icon_name and self.screen_theme:
        #     icon_name = self.screen_theme.get("icon", None)

        # logger.info(f"MessageScreen icon_name AFTER: {icon_name}")
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
        # color = self.context.get("color", theme.colors["text"])
        message_y = icon_y + icon_size + 30
        line_height = theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=color, font=info_font)
        
        logger.debug(f"MessageScreen drawn with title '{title}' and message lines: {message_lines}")


    def _load_album_image(self, path):
        """Load album image from local cache if available."""
        if not path:
            return None

        logger.debug(f"Loading album image from: {path}")
        if os.path.exists(path):
            try:
                _image = Image.open(path)
                return _image
            except Exception as e:
                logger.error(f"Failed to load cached album image: {e}")
                return None
        else:
            return None

    def _draw_icon(self, draw, x, y, size, image=None, icon_name=None):
        from app.config import config
        import os
        icon_img = None
        icon_path = None
        logger.info(f"Drawing icon '{icon_name}'") 
        if icon_name:
            # If icon_name is not a path, resolve to STATIC_FILE_PATH/icon_name.png
            if not icon_name.endswith('.png'):
                icon_path = os.path.join(config.STATIC_FILE_PATH, icon_name + ".png")
            else:
                icon_path = icon_name
            try:
                icon_img = Image.open(icon_path).convert("RGBA")
            except Exception as e:
                logger.error(f"Failed to load icon PNG '{icon_path}': {e}")
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
