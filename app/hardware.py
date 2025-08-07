"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
import RPi.GPIO as GPIO
import time
import threading
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
        
        # Ensure display is powered on and backlight is enabled
        print("💡 Ensuring display power and backlight are on...")
        self.display.power_on()
        self.display.turn_on_backlight()
        
        # Initialize RFID reader with switch-triggered mode (temporarily using button4 as switch)
        # TODO: Replace with actual microswitch when hardware is ready
        self.rfid_reader = RC522Reader(
            cs_pin=config.RFID_CS_PIN, 
            on_new_uid=self._handle_new_uid,
            switch_pin=config.NFC_CARD_SWITCH_GPIO,  # Temporarily set to Button4 GPIO in .env
            screen_manager=self.screen_manager
        )
        
        # Initialize rotary encoder with callback
        self.encoder = RotaryEncoder(pin_a=config.ROTARY_ENCODER_PIN_A, pin_b=config.ROTARY_ENCODER_PIN_B, callback=self._on_rotate, bouncetime=config.ENCODER_BOUNCETIME)
        
        # Initialize push buttons with callbacks
        self.button0 = PushButton(config.BUTTON_0_GPIO, callback=self._on_button0_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button1 = PushButton(config.BUTTON_1_GPIO, callback=self._on_button1_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button2 = PushButton(config.BUTTON_2_GPIO, callback=self._on_button2_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button3 = PushButton(config.BUTTON_3_GPIO, callback=self._on_button3_press, bouncetime=config.BUTTON_BOUNCETIME)
        # Button4 is temporarily used as NFC card switch, so not initializing as regular button
        # self.button4 = PushButton(config.BUTTON_4_GPIO, callback=self._on_button4_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button4 = None  # Temporarily disabled - GPIO used by RFID switch
        self.button5 = PushButton(config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=config.BUTTON_BOUNCETIME)

        return self.display
    
    def _handle_new_uid(self, uid):
        """Handle new RFID tag detection"""
        print(f"****New RFID tag detected: {uid}")
        
        # Import here to avoid circular imports
        from app.routes.ytmusic import create_ytmusic_entry
        from app.database import SessionLocal
        from app.models.ytmusic import YTMusicModel
        
        # Check if this RFID already exists in database
        try:
            db = SessionLocal()
            try:
                existing_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == uid).first()
                
                if existing_entry and existing_entry.yt_id and existing_entry.album_name and existing_entry.artist_name:
                    # Existing RFID with complete data - show loading album screen
                    print(f"Found existing RFID with complete data: {existing_entry.artist_name} - {existing_entry.album_name}")
                    self.screen_manager.show_rfid_loading_album(f"{existing_entry.artist_name} - {existing_entry.album_name}")
                    
                    # Trigger album playbook in Home Assistant
                    try:
                        from app.routes.homeassistant import play_album_by_id
                        result = play_album_by_id(existing_entry.yt_id)
                        if result.get("status") == "success":
                            print(f"Started playing album: {existing_entry.album_name} by {existing_entry.artist_name}")
                        else:
                            print(f"Failed to play album: {result}")
                            self.screen_manager.show_rfid_error("Failed to start playback")
                            return
                    except Exception as e:
                        print(f"Failed to trigger album playback: {e}")
                        self.screen_manager.show_rfid_error("Playback error")
                        return
                    
                    # Load data from database and update the home screen
                    from app.database import load_ytmusic_data_to_screen
                    load_ytmusic_data_to_screen(uid, self.screen_manager)
                    
                    # Schedule return to home screen after a brief delay (now it has data)
                    self._schedule_return_to_home(3.0)  # 3 seconds delay
                    
                else:
                    # New RFID or incomplete data - show new RFID screen
                    print(f"New RFID or incomplete data for {uid}")
                    self.screen_manager.show_rfid_new_card(uid)
                    
                    # Create or update YTMusic entry (this ensures the RFID is in the database)
                    create_ytmusic_entry(uid)
                    
                    # Note: The new RFID screen should stay visible until user takes action
                    # Don't automatically return to home screen for new cards
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"Failed to check database for RFID {uid}: {e}")
            self.screen_manager.show_rfid_error(f"Database error: {str(e)}")
    
    def _schedule_return_to_home(self, delay_seconds):
        """Schedule a return to appropriate screen after a delay"""
        def return_to_appropriate_screen():
            time.sleep(delay_seconds)
            print("Returning to appropriate screen...")
            self.screen_manager.show_appropriate_screen()
        
        # Start timer thread
        timer_thread = threading.Thread(target=return_to_appropriate_screen, daemon=True)
        timer_thread.start()
    
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
        """Handle button 4 press - TEMPORARILY DISABLED (used as NFC card switch)"""
        print("Button 4 press detected - but it's configured as NFC card switch!")
        print("This should trigger RFID reading instead of being a regular button.")
        # This method won't be called since button4 is not initialized as a regular button
    
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
        else:
            print("Button 4 cleanup skipped - was used as RFID switch")

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
