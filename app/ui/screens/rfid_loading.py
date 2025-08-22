import logging
logger = logging.getLogger(__name__)
from app.services import jukebox_mediaplayer
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from enum import Enum
from PIL import Image


class RfidStatus(Enum):
    READING = "reading"
    LOADING_ALBUM = "loading_album"
    NEW_RFID = "new_rfid"
    ERROR = "error"


# --- Individual Screen Classes ---

class RfidReadingScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "RFID Reading"
        self.status = RfidStatus.READING
        self.context = {}

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        # Draw the background
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])
        # Draw the title
        title_font = self.theme.fonts["title"]
        title_text = "NFC Card Reader"
        title_bbox = draw_context.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, self.theme.layout["title_y"]), title_text, fill=self.theme.colors["text"], font=title_font)
        # Draw the icon
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, self.theme.fonts, image=image)
        # Draw the message
        message_y = icon_y + icon_size + 30
        info_y = self.height - 60
        self._draw_reading(draw_context, fonts, context, message_y, info_y)

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        from app.config import ICON_DEFINITIONS
        icon_name = "contactless"
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
        logger.debug(f"Using icon '{icon_name}' for status 'READING'")
        icon_img = None
        if icon_def:
            from app.ui.manager import ScreenManager
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
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

    def _draw_reading(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        message = "Reading NFC card..."
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)


class RfidLoadingScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "RFID Loading Album"
        self.status = RfidStatus.LOADING_ALBUM
        self.context = {}

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])
        title_font = self.theme.fonts["title"]
        title_text = "NFC Card Reader"
        title_bbox = draw_context.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, self.theme.layout["title_y"]), title_text, fill=self.theme.colors["text"], font=title_font)
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, self.theme.fonts, image=image)
        message_y = icon_y + icon_size + 30
        info_y = self.height - 60
        self._draw_loading_album(draw_context, fonts, context, message_y, info_y)

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        from app.config import ICON_DEFINITIONS
        icon_name = "library_music"
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
        logger.debug(f"Using icon '{icon_name}' for status 'LOADING_ALBUM'")
        icon_img = None
        if icon_def:
            from app.ui.manager import ScreenManager
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
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

    def _draw_loading_album(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        album_name = context.get("album_name", "")
        message = f"Loading album: {album_name}"
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)


class RfidNewRfidScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "RFID New Card"
        self.status = RfidStatus.NEW_RFID
        self.context = {}

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])
        title_font = self.theme.fonts["title"]
        title_text = "NFC Card Reader"
        title_bbox = draw_context.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, self.theme.layout["title_y"]), title_text, fill=self.theme.colors["text"], font=title_font)
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, self.theme.fonts, image=image)
        message_y = icon_y + icon_size + 30
        info_y = self.height - 60
        self._draw_new_rfid(draw_context, fonts, context, message_y, info_y)

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        from app.config import ICON_DEFINITIONS
        icon_name = "add_circle"
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
        logger.debug(f"Using icon '{icon_name}' for status 'NEW_RFID'")
        icon_img = None
        if icon_def:
            from app.ui.manager import ScreenManager
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
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

    def _draw_new_rfid(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        rfid_id = context.get("rfid_id", "")
        message = f"New NFC card detected!\nID: {rfid_id[:8]}...\nAdding to system..."
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)
        info_text = "Please wait while we add this card to your collection..."
        info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
        info_width = info_bbox[2] - info_bbox[0]
        info_x = (self.width - info_width) // 2
        draw_context.text((info_x, info_y), info_text, fill=self.theme.colors["secondary"], font=small_font)


class RfidErrorScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "RFID Error"
        self.status = RfidStatus.ERROR
        self.context = {}

    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])
        title_font = self.theme.fonts["title"]
        title_text = "NFC Card Reader"
        title_bbox = draw_context.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, self.theme.layout["title_y"]), title_text, fill=self.theme.colors["text"], font=title_font)
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, self.theme.fonts, image=image)
        message_y = icon_y + icon_size + 30
        info_y = self.height - 60
        self._draw_error(draw_context, fonts, context, message_y, info_y)

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        from app.config import ICON_DEFINITIONS
        icon_name = "error"
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
        logger.debug(f"Using icon '{icon_name}' for status 'ERROR'")
        icon_img = None
        if icon_def:
            from app.ui.manager import ScreenManager
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
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

    def _draw_error(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        error_message = context.get("error_message", "")
        message = f"Error: {error_message}"
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)
        info_text = "Please try again or check the card"
        info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
        info_width = info_bbox[2] - info_bbox[0]
        info_x = (self.width - info_width) // 2
        draw_context.text((info_x, info_y), info_text, fill=self.theme.colors["error"], font=small_font)

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        # Use icon definitions from config.py
        from app.config import ICON_DEFINITIONS
        status_icon_map = {
            RfidStatus.READING: "contactless",
            RfidStatus.LOADING_ALBUM: "library_music",
            RfidStatus.NEW_RFID: "add_circle",
            RfidStatus.ERROR: "error"
        }
        icon_name = status_icon_map.get(self.status)
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)
        logger.debug(f"Using icon '{icon_name}' for status '{self.status}'")
        icon_img = None
        if icon_def:
            from app.ui.manager import ScreenManager
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
            except Exception as e:
                logger.error(f"Failed to load icon PNG: {e}")
        if icon_img:
            # Resize icon to fit specified size
            icon_img = icon_img.resize((size, size), resample=Image.LANCZOS)
            if image is not None:
                image.paste(icon_img, (x, y), icon_img)
            else:
                # Fallback: try draw.im.paste for custom draw wrappers
                draw.im.paste(icon_img, (x, y), icon_img)
                logger.warning(f"Custom draw wrapper used for icon '{icon_name}'")  
        else:
            # Fallback: draw a circle and a question mark
            logger.warning(f"Icon '{icon_name}' not found, using fallback")
            draw.ellipse([x, y, x + size, y + size], fill="gray", outline="black", width=2)
            draw.text((x + size // 2 - 8, y + size // 2 - 8), "?", fill="white")


    def _draw_reading(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        message = "Reading NFC card..."
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)

    def _draw_loading_album(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        album_name = context.get("album_name", "")
        message = f"Loading album: {album_name}"
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)

    def _draw_new_rfid(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        rfid_id = context.get("rfid_id", "")
        message = f"New NFC card detected!\nID: {rfid_id[:8]}...\nAdding to system..."
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)
        info_text = "Please wait while we add this card to your collection..."
        info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
        info_width = info_bbox[2] - info_bbox[0]
        info_x = (self.width - info_width) // 2
        draw_context.text((info_x, info_y), info_text, fill=self.theme.colors["secondary"], font=small_font)

    def _draw_error(self, draw_context, fonts, context, message_y, info_y):
        info_font = self.theme.fonts["info"]
        small_font = self.theme.fonts["small"]
        error_message = context.get("error_message", "")
        message = f"Error: {error_message}"
        message_lines = message.split('\n')
        line_height = self.theme.layout["line_height"]
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)
        info_text = "Please try again or check the card"
        info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
        info_width = info_bbox[2] - info_bbox[0]
        info_x = (self.width - info_width) // 2
        draw_context.text((info_x, info_y), info_text, fill=self.theme.colors["error"], font=small_font)
