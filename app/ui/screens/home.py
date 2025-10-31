import logging
import os
from app.ui.screens.base import Screen, RectElement, TextElement, ImageElement
from app.services.jukebox_mediaplayer import PlayerStatus
from app.config import config
from PIL import Image

logger = logging.getLogger(__name__)

class HomeScreen(Screen):
    def __init__(self, theme):
        super().__init__()
        self.name = "Home Screen"
        self.dirty = True
        self.context = {}
        self.current_track = None
        self.theme = theme
        self.volume = 75  
        self.player_status = PlayerStatus.STANDBY
        self.artist_name = "Unknown Artist"
        self.album_name = "Unknown Album"
        self.album_year = "----"
        self.track_title = "No Track"
        # Album identifier used to resolve static cover file from cache
        self.album_id = None
        
    @staticmethod
    def show(context=None):
        """Emit an event to show the home screen via the event bus."""
        from app.core import event_bus, EventType, Event
        event_bus.emit(Event(
            type=EventType.SHOW_HOME,
            payload=context
        ))
        logger.info(f"EventBus: Emitted 'show_home' event from HomeScreen.show()")

    def draw(self, draw_context, fonts, context=None, image=None):
        if not self.dirty:
            logger.debug("HomeScreen is not dirty, skipping draw.")
            return {"dirty": self.dirty}

        self.context = context
        logger.debug(f"HomeScreen.draw() called with context: {context}")
        if self.context is not None:
            self._set_context(context)
        
        logger.debug(f"HomeScreen.draw() called with context: {self.context}")        

        _padding = self.theme.layout["padding"] #20
        _volume_bar_width = self.theme.home_layout["volume_bar"]["width"] #15
        _volume_bar_height = self.theme.home_layout["volume_bar"]["height"] #200
        _album_image_size = self.theme.home_layout["album_image"]["size"] #120


        box = (0, 0, self.width, self.height)
        background_element = RectElement(*box, "white")
        background_element.draw(draw_context)

        box = (20, 10, 200, 50)
        screen_title_element = TextElement(*box, self.name, fonts["title"])
        screen_title_element.draw(draw_context)

        # Resolve static cover from local cache: /static_files/covers/{album_id}/cover-180.(webp|jpg)
        path = self._get_cover_file_path(self.album_id, size=180)
        img = self._load_album_image(path)
        box = (20, 60, 120, 120)
        album_cover_element = ImageElement(*box, img)
        album_cover_element.draw(draw_context, image)

        box = (20, 180, 400, 50)
        track_title_label_element = TextElement(*box, "Current track:", fonts["info"])
        track_title_label_element.draw(draw_context)

        box = (20, 230, 400, 50)
        track_title_element = TextElement(*box, self.track_title, fonts["title"])
        track_title_element.draw(draw_context)

        box = (160, 60, 280, 60)
        artist_name_element = TextElement(*box, self.artist_name, fonts["title"])
        artist_name_element.draw(draw_context)

        box = (160, 120, 280, 60)
        album_with_year = f"{self.album_name} ({self.album_year})"
        album_name_element = TextElement(*box, album_with_year, fonts["title"])
        album_name_element.draw(draw_context)

        box = (450, 60, _volume_bar_width, _volume_bar_height)
        volume_rect_outer = RectElement(*box, "grey")
        volume_rect_outer.draw(draw_context)

        _volume = int((self.volume / 100) * (_volume_bar_height - 4))
        box = (451, 258 - _volume, _volume_bar_width-2, _volume)
        volume_rect_inner = RectElement(*box, "green")
        volume_rect_inner.draw(draw_context)

        box = (450, 260, 30, 20)
        volume_value_element = TextElement(*box, f"{self.volume}%", fonts["small"])
        volume_value_element.draw(draw_context)

        path = self._get_icon_filename()
        img = self._load_album_image(path)
        box = (450, 280, 30, 30)
        player_status_element = ImageElement(*box, img)
        player_status_element.draw(draw_context, image)

        return {"dirty": self.dirty}

    def is_dirty(self):
        self.dirty = True
        return self.dirty

    def _set_context(self, context):
        self.current_track = context.get('current_track', {})
        if self.current_track:
            self.artist_name = self.current_track.get('artist', 'Unknown Artist')
            self.track_title = self.current_track.get('title', 'No Track')
            # Playlist metadata provides 'album_cover_filename' as album_id for compatibility
            self.album_id = self.current_track.get('album_cover_filename')
            self.album_name = self.current_track.get('album', 'Unknown Album')
            self.album_year = str(self.current_track.get('year', '----'))
        else:
            self.artist_name = 'Unknown Artist'
            self.track_title = 'No Track'
            # Fallback when current_track is not set
            self.album_id = context.get('album_cover_filename')
            self.album_name = 'Unknown Album'
            self.album_year = '----'
        
        self.player_status = PlayerStatus(context.get('status', PlayerStatus.STANDBY.value))
        self.volume = context.get('volume', 0)

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

    def _get_cover_file_path(self, album_id, size=180):
        """Return local filesystem path for static cover image variants.
        Tries WebP then JPEG for the given size, falling back to the default placeholder.
        """
        if not album_id:
            return None
        try:
            base = config.STATIC_FILE_PATH
            # Candidate paths for album-specific cover
            candidates = [
                os.path.join(base, 'covers', str(album_id), f'cover-{size}.webp'),
                os.path.join(base, 'covers', str(album_id), f'cover-{size}.jpg'),
            ]
            # Fallback to default placeholder
            candidates += [
                os.path.join(base, 'covers', '_default', f'cover-{size}.webp'),
                os.path.join(base, 'covers', '_default', f'cover-{size}.jpg'),
            ]
            for p in candidates:
                if os.path.exists(p):
                    return p
        except Exception:
            pass
        return None


    def _get_icon_filename(self):
        icon_map = {
            PlayerStatus.PLAY: "play_circle",
            PlayerStatus.PAUSE: "pause_circle",
            PlayerStatus.STOP: "stop_circle",
            PlayerStatus.STANDBY: "standby_settings"
        }
        icon_name = icon_map.get(self.player_status, "?")
        icon_path = config.get_icon_path(icon_name)
        logger.debug(f"Icon path for status {self.player_status}: {icon_path}")
        return icon_path
