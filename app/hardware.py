"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
import RPi.GPIO as GPIO
from app.devices.ili9488 import ILI9488
from app.devices.rfid import RC522Reader
from app.devices.pushbutton import PushButton
from app.devices.rotaryencoder import RotaryEncoder
from app.devices.mqtt import mqtt_client, MQTT_ROOT, publish_volume, publish_discovery


class HardwareManager:
    """Manages all hardware devices and their interactions"""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.display = None
        self.rfid_reader = None
        self.encoder = None
        self.button1 = None
        self.button2 = None
        self.button3 = None
        self.button4 = None
        self.button5 = None
        self.button6 = None

    def initialize_hardware(self):
        """Initialize all hardware devices"""
        # Initialize display
        self.display = ILI9488()
        
        # Initialize RFID reader with callback
        self.rfid_reader = RC522Reader(cs_pin=7, on_new_uid=self._handle_new_uid)
        
        # Initialize rotary encoder with callback
        self.encoder = RotaryEncoder(pin_a=6, pin_b=5, callback=self._on_rotate)
        
        # Initialize push buttons with callbacks
        self.button1 = PushButton(17, callback=self._on_button_press) #rotary encoder button
        self.button2 = PushButton(19, callback=self._on_button_press)
        self.button3 = PushButton(26, callback=self._on_button_press)
        self.button4 = PushButton(12, callback=self._on_button_press)
        self.button5 = PushButton(14, callback=self._on_button_press)
        self.button6 = PushButton(15, callback=self._on_button_press)

        return self.display
    
    def _handle_new_uid(self, uid):
        """Handle new RFID tag detection"""
        print(f"****New RFID tag detected: {uid}")
        display_text = f"RFID UID: {uid}"
        
        # Publish to MQTT
        try:
            mqtt_client.publish(f"{MQTT_ROOT}/test", display_text)
        except Exception as e:
            print(f"Failed to publish RFID to MQTT: {e}")
        
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
    
    def _on_button_press(self):
        """Handle button press events"""
        print("Button was pressed! Switching to next screen...")
        #self.screen_manager.next_screen()
    
    def _on_rotate(self, position, direction):
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
            
            # Publish volume change to MQTT for other components
            try:
                publish_volume(new_volume)
            except Exception as e:
                print(f"Failed to publish volume to MQTT: {e}")
            
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

        if self.button6:
            try:
                self.button6.cleanup()
            except Exception as e:
                print(f"Button 6 cleanup error: {e}")

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
