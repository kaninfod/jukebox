
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
from app.ui.screens.rfid_loading import RfidStatus

import logging

logger = logging.getLogger(__name__)


class HardwareManager:
    """Manages all hardware devices and their interactions"""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.playback_manager = None
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

        # Initialize RFID reader (no switch logic inside the driver)
        self.rfid_reader = RC522Reader(
            cs_pin=config.RFID_CS_PIN,
            on_new_uid=self._handle_new_uid
        )

        # Set up switch pin for RFID (external to device driver)
        self.rfid_switch_pin = config.NFC_CARD_SWITCH_GPIO  #if hasattr(config, 'NFC_CARD_SWITCH_GPIO') else config.BUTTON_4_GPIO
        GPIO.setup(self.rfid_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.rfid_switch_pin, GPIO.FALLING, callback=self._on_rfid_switch_activated, bouncetime=500)
        logger.info(f"RFID switch monitoring started on GPIO {self.rfid_switch_pin}")

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

    def _on_rfid_switch_activated(self, channel):
        """Handle switch activation (card inserted) for RFID. Only trigger on actual FALLING edge (LOW)."""
        # Only proceed if the pin is actually LOW (FALLING edge)
        if not self.rfid_reader or not self.rfid_reader.initialized or self.rfid_reader.reading_active or GPIO.input(channel) != GPIO.LOW:
            return
        logger.info("🃏 Card insertion detected - starting RFID read...")
        # Show RFID reading screen if screen manager is available
        if self.screen_manager:
            self.screen_manager.show_rfid_reading_screen()
        # Start reading and handle result in callback
        def rfid_result_callback(result):
            # Called from RFID reader thread when done
            _callback_result_status = result.get('status')
            logger.info(f"RFID read result: {_callback_result_status}")
            if not self.screen_manager:
                return
            if _callback_result_status == "success":
                # Let the normal new UID handler take over (already called by RC522Reader)
                pass
            elif _callback_result_status == "timeout":
                self.screen_manager.show_error_screen({
                    "status": "error",
                    "error_message": result.get("error_message", "Card read timeout.")
                })
            elif _callback_result_status == "error":
                self.screen_manager.show_rfid_error_screen({
                    "status": "error",
                    "error_message": result.get("error_message", "RFID error.")
                })
        self.rfid_reader.start_reading(result_callback=rfid_result_callback)
    

    def _handle_new_uid(self, uid):
        try:
            from app.main import playback_manager
            result = playback_manager.load_rfid(rfid=uid)

        except Exception as e:
            logger.error(f"Failed to call playback manager: {e}")
            return
    
    def _on_button0_press(self):
        """Handle button 0 press - Generic button"""
        logger.info("Button 0 was pressed!")
    
    def _on_button1_press(self):
        """Handle button 1 press - Previous track"""
        result = self.playback_manager.player.previous_track()
        logger.info(f"Previous track: {result}")

    def _on_button2_press(self):
        """Handle button 2 press - Play/Pause"""
        result = self.playback_manager.player.play_pause()
        logger.info(f"Play/Pause: {result}")
    
    def _on_button3_press(self):
        """Handle button 3 press - Next track"""
        result = self.playback_manager.player.next_track()
        logger.info(f"Next track: {result}")
    
    def _on_button4_press(self):
        """Handle button 4 press - TEMPORARILY DISABLED (used as NFC card switch)"""
        logger.info("Button 4 press detected")
    
    def _on_button5_press(self):
        """Handle button 5 press - Rotary encoder button"""
        logger.info("Rotary encoder button was pressed!")
        #self.screen_manager.next_screen()
    
    def _on_rotate(self, direction, position):
        """Handle rotary encoder rotation"""
        #logger.debug(f"Rotary encoder moved to {position}, direction: {'CW' if direction > 0 else 'CCW'}")
        if direction > 0:
            self.playback_manager.player.volume_up()
        else:
            self.playback_manager.player.volume_down()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        # Clean up individual devices first (while GPIO mode is still set)               
        if self.rfid_reader:
            try:
                self.rfid_reader.stop()
            except Exception as e:
                logger.error(f"RFID cleanup error: {e}")
        # Remove RFID switch event detection
        if hasattr(self, 'rfid_switch_pin'):
            try:
                GPIO.remove_event_detect(self.rfid_switch_pin)
                logger.info(f"RFID switch event detection removed from GPIO {self.rfid_switch_pin}")
            except Exception as e:
                logger.error(f"Error removing RFID switch event detection: {e}")
                
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
