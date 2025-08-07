"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
import RPi.GPIO as GPIO
from app.config import config
from app.devices.ili9488 import ILI9488
from app.devices.rfid import RC522Reader
from app.devices.pushbutton import PushButton
from app.devices.rotaryencoder import RotaryEncoder
from app.routes.homeassistant import (
    next_track_on_ytube_music_player, 
    previous_track_on_ytube_music_player,
    play_pause_ytube_music_player,
    stop_ytube_music_player
)


class HardwareManager:
    """Manages all hardware devices and their interactions"""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.display = None
        self.rfid_reader = None
        self.encoder = None
        self.button0 = None
        self.button1 = None
        self.button2 = None
        self.button3 = None
        self.button4 = None
        self.button5 = None

    def initialize_hardware(self):
        """Initialize all hardware devices"""
        # Initialize display
        self.display = ILI9488()
        
        # Initialize RFID reader with callback
        self.rfid_reader = RC522Reader(cs_pin=config.RFID_CS_PIN, poll_interval=config.RFID_POLL_INTERVAL, on_new_uid=self._handle_new_uid)
        
        # Initialize rotary encoder with callback
        self.encoder = RotaryEncoder(pin_a=config.ROTARY_ENCODER_PIN_A, pin_b=config.ROTARY_ENCODER_PIN_B, callback=self._on_rotate, bouncetime=config.ENCODER_BOUNCETIME)
        
        # Initialize push buttons with callbacks
        self.button0 = PushButton(config.BUTTON_0_GPIO, callback=self._on_button0_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button1 = PushButton(config.BUTTON_1_GPIO, callback=self._on_button1_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button2 = PushButton(config.BUTTON_2_GPIO, callback=self._on_button2_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button3 = PushButton(config.BUTTON_3_GPIO, callback=self._on_button3_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button4 = PushButton(config.BUTTON_4_GPIO, callback=self._on_button4_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button5 = PushButton(config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=config.BUTTON_BOUNCETIME)

        return self.display
    
    def _handle_new_uid(self, uid):
        """Handle new RFID tag detection"""
        print(f"****New RFID tag detected: {uid}")
        
        # Import here to avoid circular imports
        from app.routes.ytmusic import create_ytmusic_entry
        from app.database import SessionLocal
        from app.models.ytmusic import YTMusicModel
        
        # Create or update YTMusic entry (this just ensures the RFID is in the database)
        create_ytmusic_entry(uid)
        
        # Check if this RFID has a database entry with complete data
        try:
            db = SessionLocal()
            try:
                entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == uid).first()
                
                # Only proceed if we have a complete entry with yt_id and meaningful data
                if (entry and 
                    entry.yt_id and 
                    entry.album_name and 
                    entry.artist_name and
                    entry.album_name != "Unknown Album" and
                    entry.artist_name != "Unknown Artist"):
                    
                    print(f"Found complete database entry for {uid}: {entry.artist_name} - {entry.album_name}")
                    
                    # Trigger album playback in Home Assistant
                    try:
                        from app.routes.homeassistant import play_album_by_id
                        result = play_album_by_id(entry.yt_id)
                        if result.get("status") == "success":
                            print(f"Started playing album: {entry.album_name} by {entry.artist_name}")
                        else:
                            print(f"Failed to play album: {result}")
                    except Exception as e:
                        print(f"Failed to trigger album playback: {e}")
                    
                    # Load data from database and update the home screen
                    from app.database import load_ytmusic_data_to_screen
                    load_ytmusic_data_to_screen(uid, self.screen_manager)
                    
                else:
                    if not entry:
                        print(f"No database entry found for RFID {uid}")
                    elif not entry.yt_id:
                        print(f"RFID {uid} has no yt_id, skipping playback and display update")
                    else:
                        print(f"RFID {uid} has incomplete data (missing album/artist info), skipping playback and display update")
                    
                    # Don't update display or trigger playback for incomplete entries
                    
            finally:
                db.close()
        except Exception as e:
            print(f"Failed to check database for RFID {uid}: {e}")
    
    def _on_button0_press(self):
        """Handle button 0 press - Generic button"""
        print("Button 0 was pressed!")
        #self.screen_manager.next_screen()
    
    def _on_button1_press(self):
        """Handle button 1 press - Previous track"""
        result = previous_track_on_ytube_music_player()
        print(f"Previous track: {result}")

    def _on_button2_press(self):
        """Handle button 2 press - Play/Pause"""
        result = play_pause_ytube_music_player()
        print(f"Play/Pause: {result}")
    
    def _on_button3_press(self):
        """Handle button 3 press - Next track"""
        result = next_track_on_ytube_music_player()
        print(f"Next track: {result}")
    
    def _on_button4_press(self):
        """Handle button 4 press - Stop"""
        result = stop_ytube_music_player()
        print(f"Stop: {result}")
    
    def _on_button5_press(self):
        """Handle button 5 press - Rotary encoder button"""
        print("Rotary encoder button was pressed!")
        #self.screen_manager.next_screen()
    
    def _on_rotate(self, direction, position):
        """Handle rotary encoder rotation"""
        #print(f"Rotary encoder moved to {position}, direction: {'CW' if direction > 0 else 'CCW'}")
        
        # Update volume based on rotary encoder
        home_screen = self.screen_manager.screens.get('home')
        if home_screen:
            current_volume = home_screen.volume
            new_volume = current_volume + (5 * direction)  # 5% steps
            new_volume = max(0, min(100, new_volume))  # Clamp between 0-100
            
            # Update the screen volume
            home_screen.set_volume(new_volume)
            
            # Re-render if we're on the home screen to show visual feedback
            if self.screen_manager.current_screen == home_screen:
                self.screen_manager.render()
            
            # Sync volume change to Home Assistant using the router function
            try:
                from app.routes.homeassistant import set_volume_by_percent
                result = set_volume_by_percent(new_volume)
                if result.get("status") == "success":
                    print(f"Volume synced to HA: {new_volume}%")
                else:
                    print(f"Failed to sync volume to HA: {result}")
            except Exception as e:
                print(f"Failed to sync volume to Home Assistant: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        # Clean up individual devices first (while GPIO mode is still set)               
        if self.rfid_reader:
            try:
                self.rfid_reader.stop()
            except Exception as e:
                print(f"RFID cleanup error: {e}")
                
        if self.encoder:
            try:
                self.encoder.cleanup()
            except Exception as e:
                print(f"Encoder cleanup error: {e}")
        
        # Clean up buttons using their cleanup methods
        if self.button0:
            try:
                self.button0.cleanup()
            except Exception as e:
                print(f"Button 0 cleanup error: {e}")
            
        if self.button1:
            try:
                self.button1.cleanup()
            except Exception as e:
                print(f"Button 1 cleanup error: {e}")

        if self.button2:
            try:
                self.button2.cleanup()
            except Exception as e:
                print(f"Button 2 cleanup error: {e}")

        if self.button3:
            try:
                self.button3.cleanup()
            except Exception as e:
                print(f"Button 3 cleanup error: {e}")

        if self.button4:
            try:
                self.button4.cleanup()
            except Exception as e:
                print(f"Button 4 cleanup error: {e}")

        if self.button5:
            try:
                self.button5.cleanup()
            except Exception as e:
                print(f"Button 5 cleanup error: {e}")

        # Clean up display last
        if self.display:
            try:
                self.display.cleanup()
            except Exception as e:
                print(f"Display cleanup error: {e}")
        
        # Final GPIO cleanup
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Final GPIO cleanup error: {e}")
