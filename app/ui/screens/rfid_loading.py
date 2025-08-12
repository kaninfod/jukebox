import logging
logger = logging.getLogger(__name__)
from app.ui.theme import UITheme
from app.ui.screens.base import Screen
from enum import Enum
from PIL import Image

class RfidLoadingStatus(Enum):
    READING = "reading"
    LOADING_ALBUM = "loading_album"
    NEW_RFID = "new_rfid"
    ERROR = "error"

class RfidLoadingScreen(Screen):
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "RFID Loading"
        self.status = RfidLoadingStatus.READING
        self.message = ""
        self.album_name = ""
        self.rfid_id = ""
        self.error_message = ""
        self.start_time = None
        self.context = {}

    def set_reading(self):
        self.status = RfidLoadingStatus.READING
        self.message = "Reading NFC card..."
        self.dirty = True

    def set_loading_album(self, album_name):
        self.status = RfidLoadingStatus.LOADING_ALBUM
        self.album_name = album_name
        self.message = f"Loading album: {album_name}"
        self.dirty = True

    def set_new_rfid(self, rfid_id):
        self.status = RfidLoadingStatus.NEW_RFID
        self.rfid_id = rfid_id
        self.message = f"New NFC card detected!\nID: {rfid_id[:8]}...\nAdding to system..."
        self.dirty = True

    def set_error(self, error_message):
        self.status = RfidLoadingStatus.ERROR
        self.error_message = error_message
        self.message = f"Error: {error_message}"
        self.dirty = True

    def _draw_status_icon(self, draw, x, y, size, fonts, image=None):
        # Use icon definitions from config.py
        from app.config import ICON_DEFINITIONS
        status_icon_map = {
            RfidLoadingStatus.READING: "contactless",
            RfidLoadingStatus.LOADING_ALBUM: "library_music",
            RfidLoadingStatus.NEW_RFID: "add_circle",
            RfidLoadingStatus.ERROR: "error"
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


    def draw(self, draw_context, fonts, context=None, image=None):
        self.context = context or {}
        self.status = self.context.get("status", RfidLoadingStatus.READING)

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
        draw_context.text((title_x, self.theme.layout["title_y"]), title_text, fill=self.theme.colors["text"], font=title_font)
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, self.theme.fonts, image=image)

        # Draw the message
        message_y = icon_y + icon_size + 30
        info_y = self.height - 60
        if self.status == RfidLoadingStatus.READING:
            self._draw_reading(draw_context, fonts, self.context, message_y, info_y)
        elif self.status == RfidLoadingStatus.LOADING_ALBUM:
            self._draw_loading_album(draw_context, fonts, self.context, message_y, info_y)
        elif self.status == RfidLoadingStatus.NEW_RFID:
            self._draw_new_rfid(draw_context, fonts, self.context, message_y, info_y)
        elif self.status == RfidLoadingStatus.ERROR:
            self._draw_error(draw_context, fonts, self.context, message_y, info_y)

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
        album_name = self.context.get("album_name", "") if self.context else ""
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
        rfid_id = self.context.get("rfid_id", "") if self.context else ""
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
        error_message = self.context.get("error_message", "") if self.context else ""
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
