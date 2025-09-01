import logging
from app.ui.theme import UITheme as theme
from app.ui.screens.base import Screen
from app.services.jukebox_mediaplayer import PlayerStatus
from PIL import Image

logger = logging.getLogger(__name__)

class HomeScreen(Screen):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.volume = 75  
        self.player_status = PlayerStatus.STANDBY
        self.artist_name = "Unknown Artist"
        self.album_name = "Unknown Album"
        self.album_year = "----"
        self.track_title = "No Track"
        self.album_image_url = None
        self.album_image = None
        self.context = {}
        self.dirty = True
        self.name = "Home Screen"

    @staticmethod
    def show(context=None):
        """Emit an event to show the home screen via the event bus."""
        # from app.core.event_bus import event_bus, Event
        # event_bus.emit(Event(type="show_home", payload=context))
        from app.core import event_bus, EventType, Event
        event_bus.emit(Event(
            type=EventType.SHOW_HOME,
            payload=context
        ))

        # from app.core import event_bus, EventFactory
        # event_bus.emit(EventFactory.show_home(payload=context))
        logger.info(f"EventBus: Emitted 'show_home' event from HomeScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        if not self.dirty:
            logger.debug("HomeScreen is not dirty, skipping draw.")
            return {"dirty": self.dirty}

        self.context = context

        # Extract state from unified context dict, supporting nested 'current_track'
        if self.context is not None:
            track = self.context.get('current_track', {})
            self.artist_name = track.get('artist') or self.context.get('artist', 'Unknown Artist')
            self.track_title = track.get('title') or self.context.get('title', 'No Track')
            # Prefer album_cover_filename from context (cached filename from DB)
            self.album_image_url = self.context.get('album_cover_filename')
            self.volume = self.context.get('volume', 0)
            self.album_name = track.get('album') or self.context.get('album', 'Unknown Album')
            self.album_year = track.get('year') or self.context.get('year', '----')
            status_str = self.context.get('status', PlayerStatus.STANDBY.value)
            try:
                self.player_status = PlayerStatus(status_str)
            except ValueError:
                self.player_status = PlayerStatus.STANDBY
            
        self._draw_background(draw_context)
        self._draw_screen_title(draw_context, fonts)
        self._draw_album_image(draw_context, image)
        self._draw_artist_and_album(draw_context, fonts)
        self._draw_current_track_label(draw_context, fonts)
        self._draw_track_title(draw_context, fonts)
        self._draw_volume_bar(draw_context, fonts)
        self._draw_status_icon(draw_context, fonts, image)
        self.dirty = False
        return {"dirty": self.dirty}

    def is_dirty(self):
        self.dirty = True
        return self.dirty


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
   
        if self.album_image is not None and image is not None:
            try:
                draw_context.rectangle([image_x, image_y, image_x + image_size, image_y + image_size], outline=self.theme.colors["highlight"], fill=None)
                draw_context.text((image_x + 30, image_y + 55), "LOADED", fill=self.theme.colors["highlight"])
                mask = self.album_image if self.album_image.mode == 'RGBA' else None
                image.paste(self.album_image, (image_x, image_y), mask)
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
        from app.config import config
        from app.ui.manager import ScreenManager
        
        status_icon_size = 30
        volume_bar_width = self.theme.home_layout["volume_bar"]["width"]
        volume_x = self.width - volume_bar_width - self.theme.layout["padding"]
        volume_bar_height = self.theme.home_layout["volume_bar"]["height"]
        volume_y = self.theme.layout["padding"]
        status_x = volume_x - 8
        status_y = volume_y + volume_bar_height + 40
        
        icon_map = {
            PlayerStatus.PLAY: "play_circle",
            PlayerStatus.PAUSE: "pause_circle",
            PlayerStatus.STOP: "stop_circle",
            PlayerStatus.STANDBY: "standby_settings"
        }
        icon_name = icon_map.get(self.player_status, "?")
        icon_path = config.get_icon_path(icon_name)
        if icon_path:
            try:
                icon_img = Image.open(icon_path).convert("RGBA")
                #icon_img = ScreenManager.get_icon_png(icon_path)
            except Exception as e:
                logger.error(f"Failed to load icon PNG: {e}")
        if icon_img and image is not None:
            # Resize icon to fit specified size
            icon_img = icon_img.resize((status_icon_size, status_icon_size), resample=Image.LANCZOS)
            image.paste(icon_img, (status_x, status_y), icon_img)
        else:
            # Fallback: draw a circle and a question mark
            draw_context.ellipse([status_x, status_y, status_x + status_icon_size, status_y + status_icon_size], fill="gray", outline="black", width=2)
            draw_context.text((status_x + status_icon_size // 2 - 8, status_y + status_icon_size // 2 - 8), "?", fill="white")

    def _load_album_image(self):
        """Load album image from local cache if available."""
        from app.config import config
        import os
        from PIL import Image
        if not self.album_image_url:
            self.album_image = None
            return
        local_path = config.get_image_path(self.album_image_url)
        
        if os.path.exists(local_path):
            try:
                self.album_image = Image.open(local_path)
            except Exception as e:
                logger.error(f"Failed to load cached album image: {e}")
                self.album_image = None
        else:
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