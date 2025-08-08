from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from enum import Enum

class PlayerStatus(Enum):
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    STANDBY = "standby"

class RfidLoadingStatus(Enum):
    """RFID loading status enumeration"""
    READING = "reading"
    LOADING_ALBUM = "loading_album"
    NEW_RFID = "new_rfid"
    ERROR = "error"

class Screen:
    """Base class for all screens"""
    def __init__(self, width=480, height=320):
        self.width = width
        self.height = height
        self.name = "Base Screen"
        self.dirty = True  # Mark as needing redraw initially
    
    def draw(self, draw_context, fonts, context=None):
        """Override this method in subclasses"""
        pass

class IdleScreen(Screen):
    """Screen for showing welcome message when no music is playing"""
    
    def __init__(self, theme, width=480, height=320):
        super().__init__(width, height)
        self.theme = theme
        self.name = "Idle Screen"
    
    def add_screen(self, name, screen):
        """Add a screen to the manager"""
        self.screens[name] = screen
        if name not in self.screen_order:
            self.screen_order.append(name)
    
    def switch_to_screen(self, screen_name):
        """Switch to a specific screen by name (no render)"""
        if self.current_screen and self.current_screen.name == screen_name:
            print(f"Screen already {screen_name}; skipping switch.")
            return
        old_screen = self.current_screen.name if self.current_screen else "None"
        self.current_screen = self.screens[screen_name]
        self.current_screen_index = self.screen_order.index(screen_name)
        print(f"🖥️  SCREEN CHANGE: {old_screen} → {self.current_screen.name}")
        # No render here!

    def update_player_status(self, new_status):
        if new_status != self.last_player_status:
            self.last_player_status = new_status
            print(f"Player status changed to {new_status}; updating screen.")
            self.show_appropriate_screen()
        else:
            print("No change in player status; skipping update.")

    def update_track_info(self, new_track_info):
        if new_track_info != self.last_track_info:
            self.last_track_info = new_track_info
            print("Track info changed; updating screen.")
            self.show_appropriate_screen()
        else:
            print("No change in track info; skipping update.")

    def update_rfid_id(self, new_rfid_id):
        if new_rfid_id != self.last_rfid_id:
            self.last_rfid_id = new_rfid_id
            print(f"RFID ID changed to {new_rfid_id}; updating screen.")
            # Call RFID-related screen logic here
        else:
            print("No change in RFID ID; skipping update.")
    
    def show_appropriate_screen(self, context=None):
        """Show idle screen if no music or music is stopped, otherwise home screen"""
        home_screen = self.screens.get("home")
        if (home_screen and 
            home_screen.artist_name and 
            home_screen.album_name and
            home_screen.artist_name != "Unknown Artist" and
            home_screen.album_name != "Unknown Album" and
            home_screen.player_status in [PlayerStatus.PLAY, PlayerStatus.PAUSE]):
            print("ScreenManager: Showing home screen - music is active")
            self.switch_to_screen("home")
        else:
            if home_screen and home_screen.player_status == PlayerStatus.STANDBY:
                print("ScreenManager: Showing idle screen - music is stopped")
            else:
                print("ScreenManager: Showing idle screen - no meaningful data")
            self.switch_to_screen("idle")
        # Explicitly render after switching
        self.render(context)

    def show_rfid_loading_album(self, album_name, context=None):
        """Show RFID loading album screen"""
        rfid_screen = self.screens.get("rfid_loading")
        if rfid_screen:
            rfid_screen.set_loading_album(album_name)
            self.switch_to_screen("rfid_loading")
            self.render(context)

    def show_rfid_error(self, error_message, context=None):
        """Show RFID error screen"""
        rfid_screen = self.screens.get("rfid_loading")
        if rfid_screen:
            rfid_screen.set_error(error_message)
            self.switch_to_screen("rfid_loading")
            self.render(context)

    def show_error_screen(self, error_message, context=None):
        """Show error screen"""
        error_screen = self.screens.get("error")
        if error_screen:
            error_screen.set_error(error_message)
            self.switch_to_screen("error")
            self.render(context)

    def render(self, context=None, force=False):
        """Render the current screen only if dirty or forced"""
        if self.current_screen and (self.current_screen.dirty or force):
            # Create a new image for drawing
            image = Image.new('RGB', (self.display.device.width, self.display.device.height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Draw the current screen
            self.current_screen.draw(draw, self.fonts, context)
            