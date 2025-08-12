
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
from app.ui.screens.rfid_loading import RfidLoadingStatus
import logging

logger = logging.getLogger(__name__)


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
        
        # # Ensure display is powered on and backlight is enabled
        # logger.info("💡 Ensuring display power and backlight are on...")
        # self.display.power_on()
        # self.display.turn_on_backlight()
        
        # Initialize RFID reader with switch-triggered mode (temporarily using button4 as switch)
        # TODO: Replace with actual microswitch when hardware is ready
        self.rfid_reader = RC522Reader(
            cs_pin=config.RFID_CS_PIN, 
            on_new_uid=self._handle_new_uid,
            switch_pin= config.BUTTON_0_GPIO, #config.NFC_CARD_SWITCH_GPIO,  # Temporarily set to Button4 GPIO in .env
            screen_manager=self.screen_manager
        )
        
        # Initialize rotary encoder with callback
        self.encoder = RotaryEncoder(pin_a=config.ROTARY_ENCODER_PIN_A, pin_b=config.ROTARY_ENCODER_PIN_B, callback=self._on_rotate, bouncetime=config.ENCODER_BOUNCETIME)
        
        # Initialize push buttons with callbacks
        #self.button0 = PushButton(config.BUTTON_0_GPIO, callback=self._on_button0_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button1 = PushButton(config.BUTTON_1_GPIO, callback=self._on_button1_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button2 = PushButton(config.BUTTON_2_GPIO, callback=self._on_button2_press, bouncetime=config.BUTTON_BOUNCETIME)
        self.button3 = PushButton(config.BUTTON_3_GPIO, callback=self._on_button3_press, bouncetime=config.BUTTON_BOUNCETIME)
        # Button4 is temporarily used as NFC card switch, so not initializing as regular button
        # self.button4 = PushButton(config.BUTTON_4_GPIO, callback=self._on_button4_press, bouncetime=config.BUTTON_BOUNCETIME)
        
        self.button5 = PushButton(config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=config.BUTTON_BOUNCETIME)

        return self.display
    
    def _handle_new_uid(self, uid):
        """Handle new RFID tag detection"""
        logger.info(f"****New RFID tag detected: {uid}")
        
        # Import here to avoid circular imports
        from app.routes.ytmusic import create_ytmusic_entry
        from app.database import get_ytmusic_entry_by_rfid, load_ytmusic_data_to_screen
        # Check if this RFID already exists in database
        existing_entry = get_ytmusic_entry_by_rfid(uid)
        if existing_entry and existing_entry.yt_id and existing_entry.album_name and existing_entry.artist_name:
            # Existing RFID with complete data - show loading album screen
            logger.info(f"Found existing RFID with complete data: {existing_entry.artist_name} - {existing_entry.album_name}")
            context = {
                "status": RfidLoadingStatus.LOADING_ALBUM,
                "album_name": f"{existing_entry.artist_name} - {existing_entry.album_name}"
            }
            self.screen_manager.show_rfid_screen(context)
            
            # Trigger album playhook in Home Assistant
            try:
                from app.routes.homeassistant import play_album_by_id
                result = play_album_by_id(existing_entry.yt_id)
                if result.get("status") == "success":
                    logger.info(f"Started playing album: {existing_entry.album_name} by {existing_entry.artist_name}")
                else:
                    logger.error(f"Failed to play album: {result}")
                    context = {
                        "status": "error",
                        "error_message": "Failed to start playback"
                    }
                    self.screen_manager.show_rfid_screen(context)
                    return
            except Exception as e:
                logger.error(f"Failed to trigger album playback: {e}")
                context = {
                    "status": "error",
                    "error_message": "Playback error"
                }
                self.screen_manager.show_rfid_screen(context)
                return
   
        else:
            # New RFID or incomplete data - show new RFID screen
            logger.info(f"New RFID or incomplete data for {uid}")
            context = {
                "status": "new_rfid",
                "uid": uid
            }
            self.screen_manager.show_rfid_new_card(context)
            # Create or update YTMusic entry (this ensures the RFID is in the database)
            create_ytmusic_entry(uid)

    
    def _schedule_return_to_home(self, delay_seconds):
        """Schedule a return to appropriate screen after a delay"""
        def return_to_appropriate_screen():
            time.sleep(delay_seconds)
            logger.info("Returning to appropriate screen...")
            self.screen_manager.show_appropriate_screen()
        
        # Start timer thread
        timer_thread = threading.Thread(target=return_to_appropriate_screen, daemon=True)
        timer_thread.start()
    
    def _on_button0_press(self):
        """Handle button 0 press - Generic button"""
        logger.info("Button 0 was pressed!")
        #self.screen_manager.next_screen()
    
    def _on_button1_press(self):
        """Handle button 1 press - Previous track"""
        result = previous_track_on_ytube_music_player()
        logger.info(f"Previous track: {result}")

    def _on_button2_press(self):
        """Handle button 2 press - Play/Pause"""
        result = play_pause_ytube_music_player()
        logger.info(f"Play/Pause: {result}")
    
    def _on_button3_press(self):
        """Handle button 3 press - Next track"""
        result = next_track_on_ytube_music_player()
        logger.info(f"Next track: {result}")
    
    def _on_button4_press(self):
        """Handle button 4 press - TEMPORARILY DISABLED (used as NFC card switch)"""
        logger.info("Button 4 press detected - but it's configured as NFC card switch!")
        logger.info("This should trigger RFID reading instead of being a regular button.")
        # This method won't be called since button4 is not initialized as a regular button
    
    def _on_button5_press(self):
        """Handle button 5 press - Rotary encoder button"""
        logger.info("Rotary encoder button was pressed!")
        #self.screen_manager.next_screen()
    
    def _on_rotate(self, direction, position):
        """Handle rotary encoder rotation"""
    #logger.debug(f"Rotary encoder moved to {position}, direction: {'CW' if direction > 0 else 'CCW'}")
        
        # Update volume based on rotary encoder
        home_screen = self.screen_manager.screens.get('home')
        if home_screen:
            current_volume = home_screen.volume
            new_volume = current_volume + (5 * direction)  # 5% steps
            new_volume = max(0, min(100, new_volume))  # Clamp between 0-100
            
            # Update the screen volume
            #home_screen.set_volume(new_volume)
            
            # Re-render if we're on the home screen to show visual feedback
            #if self.screen_manager.current_screen == home_screen:
            #    self.screen_manager.render()
            
            # Sync volume change to Home Assistant using the router function
            try:
                from app.routes.homeassistant import set_volume_by_percent
                result = set_volume_by_percent(new_volume)
                if result.get("status") == "success":
                    logger.info(f"Volume synced to HA: {new_volume}%")
                else:
                    logger.error(f"Failed to sync volume to HA: {result}")
            except Exception as e:
                logger.error(f"Failed to sync volume to Home Assistant: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        # Clean up individual devices first (while GPIO mode is still set)               
        if self.rfid_reader:
            try:
                self.rfid_reader.stop()
            except Exception as e:
                logger.error(f"RFID cleanup error: {e}")
                
        if self.encoder:
            try:
                self.encoder.cleanup()
            except Exception as e:
                logger.error(f"Encoder cleanup error: {e}")
        
        # Clean up buttons using their cleanup methods
        if self.button0:
            try:
                self.button0.cleanup()
            except Exception as e:
                logger.error(f"Button 0 cleanup error: {e}")
            
        if self.button1:
            try:
                self.button1.cleanup()
            except Exception as e:
                logger.error(f"Button 1 cleanup error: {e}")

        if self.button2:
            try:
                self.button2.cleanup()
            except Exception as e:
                logger.error(f"Button 2 cleanup error: {e}")

        if self.button3:
            try:
                self.button3.cleanup()
            except Exception as e:
                logger.error(f"Button 3 cleanup error: {e}")

        if self.button4:
            try:
                self.button4.cleanup()
            except Exception as e:
                logger.error(f"Button 4 cleanup error: {e}")
        else:
            logger.info("Button 4 cleanup skipped - was used as RFID switch")

        if self.button5:
            try:
                self.button5.cleanup()
            except Exception as e:
                logger.error(f"Button 5 cleanup error: {e}")

        # Clean up display last
        if self.display:
            try:
                self.display.cleanup()
            except Exception as e:
                logger.error(f"Display cleanup error: {e}")
        
        # Final GPIO cleanup
        try:
            GPIO.cleanup()
        except Exception as e:
            logger.error(f"Final GPIO cleanup error: {e}")
