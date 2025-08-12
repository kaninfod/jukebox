import logging
from app.ui.theme import UITheme as theme
from app.ui.screens.base import Screen
from enum import Enum

logger = logging.getLogger(__name__)


class PlayerStatus(Enum):
    PLAY = "playing"
    PAUSE = "paused"
    STOP = "idle"
    STANDBY = "unavailable"
    OFF = "off"

import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

class HomeScreen(Screen):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.name = "Home"
        self.volume = 75  
        self.player_status = PlayerStatus.STANDBY
        self.artist_name = "Unknown Artist"
        self.album_name = "Unknown Album"
        self.album_year = "----"
        self.track_title = "No Track"
        self.yt_id = ""
        self.album_image_url = None
        self.album_image = None
        self.context = {}
        self.dirty = True

    def set_volume(self, volume):
        """Set volume (0-100)"""
        self.volume = max(0, min(100, volume))
        self.dirty = True

    # def set_player_status(self, status):
    #     """Set player status"""
    #     if isinstance(status, PlayerStatus):
    #         self.player_status = status
    #     else:
    #         # Convert string to enum
    #         try:
    #             self.player_status = PlayerStatus(status)
    #         except ValueError:
    #             self.player_status = PlayerStatus.STANDBY
    #     self.dirty = True

    def draw(self, draw_context, fonts, context=None, image=None):
        if not self.dirty:
            logger.debug("HomeScreen is not dirty, skipping draw.")
            return {"dirty": self.dirty}

        self._set_context(context)
        self._draw_background(draw_context)
        self._draw_screen_title(draw_context, fonts)
        self._draw_album_image(draw_context, image)
        self._draw_artist_and_album(draw_context, fonts)
        self._draw_current_track_label(draw_context, fonts)
        self._draw_track_title(draw_context, fonts)
        self._draw_volume_bar(draw_context, fonts)
        self._draw_status_icon(draw_context, fonts, image)
        self.dirty = False
        return {"dirty": self.dirty, "context": self.context}

    def is_dirty(self, context):
        # Check if the new context is different from the last drawn context
        self.dirty = context != self.context
        logger.debug(f"Checking if HomeScreen is dirty with new context: {self.dirty}")
        return self.dirty
    
    def _set_context(self, context):
        self.context = context or {}
        self.yt_id = context.get("yt_id", "")
        
        db_data = self._get_album_name_from_db(self.yt_id)
        if db_data:
            self.album_name = db_data.get("album_name", "Unknown Album")
            self.album_year = db_data.get("year", "")
            logger.debug(f"Set album name from DB: {self.album_name}, year: {self.album_year}")

        self.artist_name = context.get("artist", "")
        self.track_title = context.get("track", "")
        self.album_image_url = context.get("image_url", "")
        
        self.volume = context.get("volume", 0)
        state_value = context.get("state")
        try:
            self.player_status = PlayerStatus(state_value)
        except (ValueError, TypeError, KeyError):
            self.player_status = PlayerStatus.STANDBY

    def _draw_background(self, draw_context):
        draw_context.rectangle([0, 0, self.width, self.height], fill=self.theme.colors["background"])

    def _draw_screen_title(self, draw_context, fonts):
        title_font = self.theme.fonts["title"]
        draw_context.text((self.theme.layout["padding"], self.theme.layout["title_y"]), self.name, fill=self.theme.colors["text"], font=title_font)

    def _draw_album_image(self, draw_context, image):
        image_x = self.theme.layout["padding"]
        image_y = 50
        image_size = 120
        self._load_album_image()
   
        if self.album_image is not None:
            try:
                draw_context.rectangle([image_x, image_y, image_x + image_size, image_y + image_size], outline=self.theme.colors["highlight"], fill=None)
                draw_context.text((image_x + 30, image_y + 55), "LOADED", fill=self.theme.colors["highlight"])
                mask = self.album_image if self.album_image.mode == 'RGBA' else None
                image.paste(self.album_image, (image_x, image_y), mask)
                logger.info("Album image pasted successfully (HomeScreen)")
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
                draw_context.rectangle([image_x, image_y, image_x + image_size, image_y + image_size], outline=self.theme.colors["error"], fill=None)
                draw_context.text((image_x + 35, image_y + 55), "ERROR", fill=self.theme.colors["error"])
        else:
            draw_context.rectangle([image_x, image_y, image_x + image_size, image_y + image_size], outline=self.theme.colors["text"], fill=None)
            draw_context.text((image_x + 25, image_y + 55), "NO IMAGE", fill=self.theme.colors["text"])

    def _draw_artist_and_album(self, draw_context, fonts):
        info_font = fonts.get('info', None)
        text_x = self.theme.layout["padding"] + 120 + self.theme.layout["padding"]
        text_y = 60
        line_height = self.theme.layout["line_height"]
        available_width = self.width - text_x - self.theme.layout["padding"]
        # Artist name
        artist_lines = self._wrap_text(draw_context, self.artist_name, info_font, available_width)
        for i, line in enumerate(artist_lines[:2]):
            draw_context.text((text_x, text_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)
        # Album name and year
        album_with_year = f"{self.album_name} ({self.album_year})"
        album_lines = self._wrap_text(draw_context, album_with_year, info_font, available_width)
        for i, line in enumerate(album_lines[:2]):
            draw_context.text((text_x, text_y + line_height * 2 + i * line_height), line, fill=self.theme.colors["text"], font=info_font)

    def _draw_current_track_label(self, draw_context, fonts):
        small_font = fonts.get('small', None)
        label_x = self.theme.layout["padding"]
        label_y = 50 + 120 + self.theme.layout["padding"]
        draw_context.text((label_x, label_y), "Current track", fill=self.theme.colors["text"], font=small_font)

    def _draw_track_title(self, draw_context, fonts):
        info_font = fonts.get('info', None)
        title_x = self.theme.layout["padding"] + 5
        title_y = 50 + 120 + self.theme.layout["padding"] + 20
        track_available_width = self.width - title_x - self.theme.layout["padding"]
        line_height = self.theme.layout["line_height"]
        track_lines = self._wrap_text(draw_context, self.track_title, info_font, track_available_width)
        for i, line in enumerate(track_lines[:2]):
            draw_context.text((title_x, title_y + i * line_height), line, fill=self.theme.colors["text"], font=info_font)

    def _draw_volume_bar(self, draw_context, fonts):
        volume_bar_width = self.theme.home_layout["volume_bar"]["width"]
        volume_bar_height = self.theme.home_layout["volume_bar"]["height"]
        volume_x = self.width - volume_bar_width - self.theme.layout["padding"]
        volume_y = self.theme.layout["padding"]

        draw_context.rectangle([volume_x, volume_y, volume_x + volume_bar_width, volume_y + volume_bar_height], outline="black", fill=None)
        if self.volume > 0:
            fill_height = int((self.volume / 100) * (volume_bar_height - 4))
            fill_y = volume_y + volume_bar_height - 2 - fill_height
            draw_context.rectangle([volume_x + 2, fill_y, volume_x + volume_bar_width - 2, fill_y + fill_height], outline=None, fill="green")
        volume_text = f"{self.volume}%"
        small_font = fonts.get('small', None)
        text_bbox = draw_context.textbbox((0, 0), volume_text, font=small_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw_context.text((volume_x + (volume_bar_width - text_width) // 2, volume_y + volume_bar_height + 5), volume_text, fill="black", font=small_font)

    def _draw_status_icon(self, draw_context, fonts, image):
        from app.config import ICON_DEFINITIONS
        from app.ui.manager import ScreenManager
        
        status_icon_size = 30
        volume_bar_width = self.theme.home_layout["volume_bar"]["width"]
        volume_x = self.width - volume_bar_width - self.theme.layout["padding"]
        volume_bar_height = self.theme.home_layout["volume_bar"]["height"]
        volume_y = self.theme.layout["padding"]
        status_x = volume_x
        status_y = volume_y + volume_bar_height + 40
        
        icon_map = {
            PlayerStatus.PLAY: "play_circle",
            PlayerStatus.PAUSE: "pause_circle",
            PlayerStatus.STOP: "stop_circle",
            PlayerStatus.STANDBY: "standby_settings"
        }
        icon_name = icon_map.get(self.player_status, "?")
        logger.debug(f"Current player status icon: {icon_name}")
        icon_def = next((icon for icon in ICON_DEFINITIONS if icon["name"] == icon_name), None)

        if icon_def:    
            try:
                icon_img = ScreenManager.get_icon_png(icon_def["path"])
            except Exception as e:
                logger.error(f"Failed to load icon PNG: {e}")
        if icon_img:
            # Resize icon to fit specified size
            icon_img = icon_img.resize((status_icon_size, status_icon_size), resample=Image.LANCZOS)
            if image is not None:
                image.paste(icon_img, (status_x, status_y), icon_img)
            else:
                # Fallback: try draw.im.paste for custom draw wrappers
                draw_context.im.paste(icon_img, (status_x, status_y), icon_img)
        else:
            # Fallback: draw a circle and a question mark
            draw_context.ellipse([status_x, status_y, status_x + status_icon_size, status_y + status_icon_size], fill="gray", outline="black", width=2)
            draw_context.text((status_x + status_icon_size // 2 - 8, status_y + status_icon_size // 2 - 8), "?", fill="white")

    def _load_album_image(self):
        """Load album image from URL"""
        if not self.album_image_url:
            self.album_image = None
            return
        try:
            logger.info(f"Loading image from: {self.album_image_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.album_image_url, timeout=10, headers=headers)
            logger.debug(f"Response status: {response.status_code}")
            if response.status_code == 200:
                logger.debug(f"Image data length: {len(response.content)} bytes")
                image = Image.open(BytesIO(response.content))
                logger.debug(f"Original image size: {image.size}, mode: {image.mode}")
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                self.album_image = image.resize((120, 120), Image.Resampling.LANCZOS)
                logger.info(f"Resized image to: {self.album_image.size}")
            else:
                logger.warning(f"Failed to load image: HTTP {response.status_code}")
                self.album_image = None
        except Exception as e:
            logger.error(f"Failed to load album image: {e}")
            import traceback
            traceback.print_exc()
            self.album_image = None

    def _wrap_text(self, draw, text, font, max_width):
        """Wrap text to fit within max_width, returns list of lines"""
        if not text:
            return [""]
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]



    def _get_album_name_from_db(self, yt_id):
        from app.database import get_ytmusic_data_by_yt_id
        # Try to get additional data from database using yt_id
        db_data = get_ytmusic_data_by_yt_id(yt_id) if yt_id else None
        
        # Use database data to fill in missing information, especially for album names
        if db_data:
            logger.debug(f"Found database entry for yt_id: {yt_id}")
            return {
                "album_name": db_data.get("album_name", "Unknown Album"),
                "artist_name": db_data.get("artist_name", "Unknown Artist"),
                "year": db_data.get("year", ""),
            }
        
        
            if (not media_album or 
                media_album == "Unknown Album" or 
                (db_data.get("album_name") and db_data.get("album_name") != "Unknown Album")):
                #if db_data.get("album_name"):
                logger.debug(f"WebSocket: Using database album name: {db_data.get('album_name')} (HA provided: {media_album})")
                media_album = db_data.get("album_name")
            
            # Use database data for other fields if HA data is missing or generic
            if not media_artist or media_artist == "Unknown Artist":
                media_artist = db_data.get("artist_name") or media_artist
            
            # Always use database year and thumbnail if available (HA rarely provides these)
            media_year = str(db_data.get("year", "")) if db_data.get("year") else ""
            if db_data.get("thumbnail"):
                media_image = db_data.get("thumbnail")

