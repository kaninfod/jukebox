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
    
    def draw(self, draw_context, fonts, context=None):
        """Override this method in subclasses"""
        pass

class IdleScreen(Screen):
    """Screen for showing welcome message when no music is playing"""
    
    def __init__(self, width=480, height=320):
        super().__init__(width, height)
        self.name = "Idle Screen"
    
    def draw(self, draw_context, fonts, context=None):
        """Draw the idle/welcome screen"""
        # Clear background to white
        draw_context.rectangle([0, 0, self.width, self.height], fill="white")
        
        # Get fonts
        title_font = fonts.get('title', None)
        info_font = fonts.get('info', None)
        small_font = fonts.get('small', None)
        
        # Center everything on the screen
        center_x = self.width // 2
        
        # Welcome text (top)
        welcome_text = "Welcome to"
        if title_font:
            welcome_bbox = draw_context.textbbox((0, 0), welcome_text, font=title_font)
            welcome_width = welcome_bbox[2] - welcome_bbox[0]
            welcome_x = center_x - (welcome_width // 2)
        else:
            welcome_x = center_x - 50  # Fallback positioning
        
        draw_context.text((welcome_x, 50), welcome_text, fill="black", font=title_font)
        
        # Company name (larger, bold effect with offset)
        company_text = "Siemens"
        if info_font:
            company_bbox = draw_context.textbbox((0, 0), company_text, font=info_font)
            company_width = company_bbox[2] - company_bbox[0]
            company_x = center_x - (company_width // 2)
        else:
            company_x = center_x - 40  # Fallback positioning
        
        # Draw text with bold effect (slight offset)
        draw_context.text((company_x + 1, 91), company_text, fill="gray", font=info_font)  # Shadow
        draw_context.text((company_x, 90), company_text, fill="black", font=info_font)     # Main text
        
        # Product name
        product_text = "Klangmeister RG406"
        if info_font:
            product_bbox = draw_context.textbbox((0, 0), product_text, font=info_font)
            product_width = product_bbox[2] - product_bbox[0]
            product_x = center_x - (product_width // 2)
        else:
            product_x = center_x - 60  # Fallback positioning
        
        draw_context.text((product_x, 130), product_text, fill="blue", font=info_font)
        
        # Decorative line
        line_y = 180
        line_start_x = center_x - 100
        line_end_x = center_x + 100
        draw_context.line([(line_start_x, line_y), (line_end_x, line_y)], fill="blue", width=2)
        
        # Instruction text
        instruction_text = "Scan a card to proceed..."
        if small_font:
            instruction_bbox = draw_context.textbbox((0, 0), instruction_text, font=small_font)
            instruction_width = instruction_bbox[2] - instruction_bbox[0]
            instruction_x = center_x - (instruction_width // 2)
        else:
            instruction_x = center_x - 80  # Fallback positioning
        
        draw_context.text((instruction_x, 220), instruction_text, fill="gray", font=small_font)
        
        # Optional: Add a simple RFID card icon placeholder
        # Draw a simple rectangle to represent a card
        card_width = 60
        card_height = 40
        card_x = center_x - (card_width // 2)
        card_y = 260
        
        # Card outline
        draw_context.rectangle([card_x, card_y, card_x + card_width, card_y + card_height], 
                              outline="black", fill="white", width=2)
        
        # Card "chip" (small rectangle)
        chip_size = 8
        chip_x = card_x + 10
        chip_y = card_y + 10
        draw_context.rectangle([chip_x, chip_y, chip_x + chip_size, chip_y + chip_size], 
                              fill="gold", outline="black")
        
        # Card text
        if small_font:
            draw_context.text((card_x + 20, card_y + 22), "NFC", fill="black", font=small_font)

class HomeScreen(Screen):
    def __init__(self):
        super().__init__()
        self.name = "Home"
        self.volume = 75  # Start with higher volumen
        self.player_status = PlayerStatus.STANDBY
        self.artist_name = "Unknown Artist"
        self.album_name = "Unknown Album"
        self.album_year = "----"
        self.track_title = "No Track"
        self.yt_id = ""
        self.album_image_url = None
        self.album_image = None
    
    def set_volume(self, volume):
        """Set volume (0-100)"""
        self.volume = max(0, min(100, volume))
    
    def set_player_status(self, status):
        """Set player status"""
        if isinstance(status, PlayerStatus):
            self.player_status = status
        else:
            # Convert string to enum
            try:
                self.player_status = PlayerStatus(status)
            except ValueError:
                self.player_status = PlayerStatus.STANDBY
    
    def set_track_info(self, artist="", album="", year="", track="", image_url=None, yt_id=""):
        """Set current track information"""
        self.artist_name = artist or "Unknown Artist"
        self.album_name = album or "Unknown Album"
        self.album_year = str(year) if year else "----"
        self.track_title = track or "No Track"
        self.yt_id = yt_id or ""
        
        if image_url != self.album_image_url:
            self.album_image_url = image_url
            self._load_album_image()
    
    def _load_album_image(self):
        """Load album image from URL"""
        if not self.album_image_url:
            self.album_image = None
            return
        
        try:
            print(f"Loading image from: {self.album_image_url}")
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.album_image_url, timeout=10, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"Image data length: {len(response.content)} bytes")
                image = Image.open(BytesIO(response.content))
                print(f"Original image size: {image.size}, mode: {image.mode}")
                
                # Convert to RGB if needed (in case it's RGBA or other mode)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Resize to 120x120
                self.album_image = image.resize((120, 120), Image.Resampling.LANCZOS)
                print(f"Resized image to: {self.album_image.size}")
            else:
                print(f"Failed to load image: HTTP {response.status_code}")
                self.album_image = None
        except Exception as e:
            print(f"Failed to load album image: {e}")
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
            # Test if adding this word would exceed max_width
            test_line = current_line + (" " if current_line else "") + word
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                # Current line is full, start a new line
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, force it on a line anyway
                    lines.append(word)
        
        # Add the last line if there's content
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]

    def _draw_volume_bar(self, draw, x, y, width, height, fonts):
        """Draw vertical volume bar"""
        # Outer rectangle (border)
        draw.rectangle([x, y, x + width, y + height], outline="black", fill=None)
        
        # Inner rectangle (volume level)
        if self.volume > 0:
            fill_height = int((self.volume / 100) * (height - 4))  # -4 for padding
            fill_y = y + height - 2 - fill_height  # Start from bottom
            draw.rectangle([x + 2, fill_y, x + width - 2, y + height - 2], 
                          outline=None, fill="green")
        
        # Volume percentage text below
        volume_text = f"{self.volume}%"
        small_font = fonts.get('small', None)
        text_bbox = draw.textbbox((0, 0), volume_text, font=small_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((x + (width - text_width) // 2, y + height + 5), 
                 volume_text, fill="black", font=small_font)
    
    def _draw_status_icon(self, draw, x, y, size, fonts):
        """Draw player status icon using symbol font"""
        # Symbol font keyboard mappings
        icon_map = {
            PlayerStatus.PLAY: "1",      # Play symbol
            PlayerStatus.PAUSE: "2",     # Pause symbol
            PlayerStatus.STOP: "3",      # Stop symbol
            PlayerStatus.STANDBY: "q"    # Standby symbol
        }
        
        icon = icon_map.get(self.player_status, "?")
        symbol_font = fonts.get('symbols', None)
        
        text_bbox = draw.textbbox((0, 0), icon, font=symbol_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the icon
        icon_x = x + (size - text_width) // 2
        icon_y = y + (size - text_height) // 2
        
        draw.text((icon_x, icon_y), icon, fill="black", font=symbol_font)
    
    def draw(self, draw_context, fonts, context=None):
        """Draw the home screen"""
        # Clear background to white
        draw_context.rectangle([0, 0, self.width, self.height], fill="white")
        
        # Screen title (upper left)
        title_font = fonts.get('title', None)
        draw_context.text((10, 10), self.name, fill="black", font=title_font)
        
        # Volume bar (right side)
        volume_bar_width = 20  # 1/3 slimmer (was 30)
        volume_bar_height = 200  # 20% longer (was 150)
        volume_x = self.width - volume_bar_width - 20
        volume_y = 20
        self._draw_volume_bar(draw_context, volume_x, volume_y, volume_bar_width, volume_bar_height, fonts)
        
        # Status icon (below volume bar)
        status_icon_size = 30
        status_x = volume_x
        status_y = volume_y + volume_bar_height + 40
        self._draw_status_icon(draw_context, status_x, status_y, status_icon_size, fonts)
        
        # Main content area
        content_x = 20
        content_y = 60
        content_width = volume_x - content_x - 20  # Space between content and volume bar
        
        # Album image (if available)
        image_size = 120
        if self.album_image:
            # Actually paste the PIL image onto the canvas
            try:
                # The draw_context is an ImageDraw object, we need the underlying Image
                # We'll handle this in the ScreenManager render method
                # For now, draw a border to show where the image should be
                draw_context.rectangle([content_x, content_y, 
                                      content_x + image_size, content_y + image_size], 
                                     outline="green", fill=None)
                draw_context.text((content_x + 30, content_y + 55), "LOADED", fill="green")
            except Exception as e:
                print(f"Error displaying image: {e}")
                draw_context.rectangle([content_x, content_y, 
                                      content_x + image_size, content_y + image_size], 
                                     outline="red", fill=None)
                draw_context.text((content_x + 35, content_y + 55), "ERROR", fill="red")
        else:
            # Placeholder for missing image
            draw_context.rectangle([content_x, content_y, 
                                  content_x + image_size, content_y + image_size], 
                                 outline="black", fill=None)
            draw_context.text((content_x + 25, content_y + 55), "NO IMAGE", fill="black")
        
        # Text information (to the right of image)
        text_x = content_x + image_size + 20
        text_y = content_y
        line_height = 25  # Reduced from 30 to fit more text
        
        info_font = fonts.get('info', None)
        
        # Calculate available width for text
        available_width = content_width - image_size - 20  # Subtract image width and spacing
        
        # Artist name (2 lines allocated)
        artist_lines = self._wrap_text(draw_context, self.artist_name, info_font, available_width)
        for i, line in enumerate(artist_lines[:2]):  # Limit to 2 lines
            draw_context.text((text_x, text_y + i * line_height), line, 
                             fill="black", font=info_font)
        text_y += line_height * 2  # Always advance by 2 lines for consistency
        
        # Album name with year (2 lines allocated)
        album_with_year = f"{self.album_name} ({self.album_year})"
        album_lines = self._wrap_text(draw_context, album_with_year, info_font, available_width)
        for i, line in enumerate(album_lines[:2]):  # Limit to 2 lines
            draw_context.text((text_x, text_y + i * line_height), line, 
                             fill="black", font=info_font)
        
        # Track title (below image, left-aligned with image)
        track_y = content_y + image_size + 20  # 20px below the image
        
        # Track label in smaller font
        small_font = fonts.get('small', None)
        draw_context.text((content_x, track_y), "Current track", 
                         fill="black", font=small_font)
        
        # Track title (indented 5px to the right from label)
        track_title_y = track_y + 20  # 20px below the label
        
        # Calculate available width for track title (full content width)
        track_available_width = content_width - 5  # Subtract the 5px indent
        
        # Wrap track title text and display up to 2 lines
        track_lines = self._wrap_text(draw_context, self.track_title, info_font, track_available_width)
        for i, line in enumerate(track_lines[:2]):  # Limit to 2 lines
            draw_context.text((content_x + 5, track_title_y + i * line_height), line, 
                             fill="black", font=info_font)

class RfidLoadingScreen(Screen):
    """Screen for showing RFID loading status"""
    
    def __init__(self, width=480, height=320):
        super().__init__(width, height)
        self.name = "RFID Loading"
        self.status = RfidLoadingStatus.READING
        self.message = ""
        self.album_name = ""
        self.rfid_id = ""
        self.error_message = ""
        self.start_time = None
        
    def set_reading(self):
        """Set status to reading RFID"""
        self.status = RfidLoadingStatus.READING
        self.message = "Reading NFC card..."
        
    def set_loading_album(self, album_name):
        """Set status to loading album"""
        self.status = RfidLoadingStatus.LOADING_ALBUM
        self.album_name = album_name
        self.message = f"Loading album: {album_name}"
        
    def set_new_rfid(self, rfid_id):
        """Set status to new RFID detected"""
        self.status = RfidLoadingStatus.NEW_RFID
        self.rfid_id = rfid_id
        self.message = f"New NFC card detected!\nID: {rfid_id[:8]}...\nAdding to system..."
        
    def set_error(self, error_message):
        """Set status to error"""
        self.status = RfidLoadingStatus.ERROR
        self.error_message = error_message
        self.message = f"Error: {error_message}"
    
    def _draw_status_icon(self, draw, x, y, size, fonts):
        """Draw status-specific icon using symbol font"""
        # Symbol font keyboard mappings for loading states
        icon_map = {
            RfidLoadingStatus.READING: "8",       # Loading/spinner symbol
            RfidLoadingStatus.LOADING_ALBUM: "1", # Play symbol (music loading)
            RfidLoadingStatus.NEW_RFID: "!",      # Exclamation/new symbol
            RfidLoadingStatus.ERROR: "X"          # Error symbol
        }
        
        # Color mapping for different states
        color_map = {
            RfidLoadingStatus.READING: "blue",
            RfidLoadingStatus.LOADING_ALBUM: "green",
            RfidLoadingStatus.NEW_RFID: "orange",
            RfidLoadingStatus.ERROR: "red"
        }
        
        icon = icon_map.get(self.status, "?")
        color = color_map.get(self.status, "black")
        symbol_font = fonts.get('symbols', None)
        
        # Draw background circle
        draw.ellipse([x, y, x + size, y + size], fill=color, outline="black", width=2)
        
        # Draw icon
        if symbol_font:
            text_bbox = draw.textbbox((0, 0), icon, font=symbol_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the icon
            icon_x = x + (size - text_width) // 2
            icon_y = y + (size - text_height) // 2
            
            draw.text((icon_x, icon_y), icon, fill="white", font=symbol_font)
    
    def _draw_progress_bar(self, draw, x, y, width, height, fonts):
        """Draw an animated progress bar for reading state"""
        if self.status != RfidLoadingStatus.READING:
            return
            
        # Draw progress bar background
        draw.rectangle([x, y, x + width, y + height], fill="lightgray", outline="black")
        
        # Simple animation - we'll make this more sophisticated later
        # For now, just show a filled bar
        progress_width = width // 2  # 50% progress as placeholder
        draw.rectangle([x, y, x + progress_width, y + height], fill="blue")
        
        # Progress text
        small_font = fonts.get('small', None)
        progress_text = "Reading NFC card..."
        text_bbox = draw.textbbox((0, 0), progress_text, font=small_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + (width - text_width) // 2
        text_y = y + height + 10
        
        draw.text((text_x, text_y), progress_text, fill="black", font=small_font)
    
    def draw(self, draw_context, fonts, context=None):
        """Draw the RFID loading screen"""
        # Clear background to white
        draw_context.rectangle([0, 0, self.width, self.height], fill="white")
        
        # Screen title (centered at top)
        title_font = fonts.get('title', None)
        title_text = "NFC Card Reader"
        title_bbox = draw_context.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw_context.text((title_x, 20), title_text, fill="black", font=title_font)
        
        # Large status icon (centered)
        icon_size = 80
        icon_x = (self.width - icon_size) // 2
        icon_y = 80
        self._draw_status_icon(draw_context, icon_x, icon_y, icon_size, fonts)
        
        # Status message (centered below icon)
        info_font = fonts.get('info', None)
        message_y = icon_y + icon_size + 30
        
        # Handle multi-line messages
        message_lines = self.message.split('\n')
        line_height = 25
        
        for i, line in enumerate(message_lines):
            line_bbox = draw_context.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (self.width - line_width) // 2
            draw_context.text((line_x, message_y + i * line_height), line, 
                             fill="black", font=info_font)
        
        # Progress bar for reading state
        if self.status == RfidLoadingStatus.READING:
            progress_y = message_y + len(message_lines) * line_height + 30
            progress_width = 300
            progress_height = 20
            progress_x = (self.width - progress_width) // 2
            self._draw_progress_bar(draw_context, progress_x, progress_y, 
                                  progress_width, progress_height, fonts)
        
        # Additional info for specific states
        small_font = fonts.get('small', None)
        info_y = self.height - 60
        
        if self.status == RfidLoadingStatus.NEW_RFID:
            info_text = "Please wait while we add this card to your collection..."
            info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
            info_width = info_bbox[2] - info_bbox[0]
            info_x = (self.width - info_width) // 2
            draw_context.text((info_x, info_y), info_text, fill="gray", font=small_font)
        
        elif self.status == RfidLoadingStatus.ERROR:
            info_text = "Please try again or check the card"
            info_bbox = draw_context.textbbox((0, 0), info_text, font=small_font)
            info_width = info_bbox[2] - info_bbox[0]
            info_x = (self.width - info_width) // 2
            draw_context.text((info_x, info_y), info_text, fill="red", font=small_font)

class ErrorScreen(Screen):
    def __init__(self, width=480, height=320, error_message=""):
        super().__init__(width, height)
        self.name = "Error"
        self.error_message = error_message

    def set_error(self, error_message):
        self.error_message = error_message

    def draw(self, draw_context, fonts, context=None):
        draw_context.rectangle([0, 0, self.width, self.height], fill="red")
        error_font = fonts.get('title', None)
        text_bbox = draw_context.textbbox((0, 0), self.error_message, font=error_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (self.width - text_width) // 2
        text_y = (self.height - text_height) // 2
        draw_context.text((text_x, text_y), self.error_message, fill="white", font=error_font)

# Update the screen factory to include ErrorScreen

def screen_factory():
    """Centralized factory for creating all screens"""
    return {
        "idle": IdleScreen(),
        "home": HomeScreen(),
        "rfid_loading": RfidLoadingScreen(),
        "error": ErrorScreen(),
        # Add more screens here as needed
    }

class UIContext:
    """Centralized UI state/context for all screens"""
    def __init__(self, player_status=None, track_info=None, rfid_status=None):
        self.player_status = player_status
        self.track_info = track_info or {}
        self.rfid_status = rfid_status or {}

class ScreenManager:
    """Manages different screens and screen switching"""
    def __init__(self, display):
        self.display = display
        self.screens = {}
        self.current_screen = None
        self.current_screen_index = 0
        self.screen_order = []
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Initialize default screens
        self._init_screens()
    
    def _load_fonts(self):
        """Load different font sizes for UI elements"""
        fonts = {}
        try:
            fonts['title'] = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 20)
            fonts['info'] = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 18)
            fonts['small'] = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 12)
            fonts['symbols'] = ImageFont.truetype("/home/pi/shared/jukebox/fonts/symbolfont/symbolfont.ttf", 24)
        except (OSError, ImportError) as e:
            print(f"Font loading failed: {e}, using default fonts")
            fonts['title'] = ImageFont.load_default()
            fonts['info'] = ImageFont.load_default()
            fonts['small'] = ImageFont.load_default()
            fonts['symbols'] = ImageFont.load_default()
        
        return fonts
    
    def _init_screens(self):
        """Initialize all screens using the factory"""
        screen_dict = screen_factory()
        for name, screen in screen_dict.items():
            self.add_screen(name, screen)
        # Set default screen to idle
        if self.screen_order:
            self.current_screen = self.screens[self.screen_order[0]]
    
    def add_screen(self, name, screen):
        """Add a screen to the manager"""
        self.screens[name] = screen
        if name not in self.screen_order:
            self.screen_order.append(name)
    
    def switch_to_screen(self, screen_name):
        """Switch to a specific screen by name (no render)"""
        if screen_name in self.screens:
            old_screen = self.current_screen.name if self.current_screen else "None"
            self.current_screen = self.screens[screen_name]
            self.current_screen_index = self.screen_order.index(screen_name)
            print(f"🖥️  SCREEN CHANGE: {old_screen} → {self.current_screen.name}")
        # No render here!

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

    def render(self, context=None):
        """Render the current screen to the display, passing UIContext"""
        if self.current_screen:
            # Create a new image for drawing
            image = Image.new('RGB', (self.display.device.width, self.display.device.height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Draw the current screen
            self.current_screen.draw(draw, self.fonts, context)
            
            # If this is the home screen and it has an album image, paste it
            if (hasattr(self.current_screen, 'album_image') and 
                self.current_screen.album_image is not None):
                try:
                    # Paste the album image at the correct position
                    content_x = 20
                    content_y = 60
                    image.paste(self.current_screen.album_image, (content_x, content_y))
                    print("Album image pasted successfully")
                except Exception as e:
                    print(f"Error pasting album image: {e}")
            
            # Display the image
            self.display.device.display(image)
