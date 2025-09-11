
"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
# Conditional GPIO import
try:
    import RPi.GPIO as GPIO
    _gpio_available = True
except ImportError:
    _gpio_available = False
    GPIO = None

from .devices.ili9488 import ILI9488
from .devices.rfid import RC522Reader
from .devices.pushbutton import PushButton
from .devices.rotaryencoder import RotaryEncoder
import logging
from app.core import EventType, Event

logger = logging.getLogger(__name__)

class HardwareManager:
    """Manages all hardware devices and their interactions"""
    
    def __init__(self, config, event_bus, screen_manager=None):
        """
        Initialize HardwareManager with dependency injection.
        
        Args:
            config: Configuration object for hardware settings
            event_bus: EventBus instance for event communication
            screen_manager: ScreenManager instance (can be set later)
        """
        # Inject dependencies - no more direct imports needed
        self.config = config
        self.event_bus = event_bus
        self.screen_manager = screen_manager
        self.playback_manager = None
        
        # Hardware device instances
        self.display = None
        self.rfid_reader = None
        self.encoder = None
        self.button0 = None
        self.button1 = None
        self.button2 = None
        self.button3 = None
        self.button4 = None
        self.button5 = None
        
        logger.info("HardwareManager initialized with dependency injection")

    def initialize_hardware(self):
        """Initialize all hardware devices using injected config"""
        if not self.config.HARDWARE_MODE or not _gpio_available:
            if not self.config.HARDWARE_MODE:
                logger.info("🖥️  Headless mode enabled - skipping hardware initialization")
            else:
                logger.info("🖥️  GPIO unavailable - falling back to headless mode")
            from .devices.mock_display import MockDisplay
            return MockDisplay()
        
        try:
            # Initialize display
            self.display = ILI9488()

            # Initialize RFID reader using injected config
            self.rfid_reader = RC522Reader(
                cs_pin=self.config.RFID_CS_PIN,
                on_new_uid=self._handle_new_uid
            )

            # Set up switch pin for RFID using injected config
            self.rfid_switch_pin = self.config.NFC_CARD_SWITCH_GPIO
            GPIO.setup(self.rfid_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.rfid_switch_pin, GPIO.FALLING, callback=self._on_rfid_switch_activated, bouncetime=500)
            logger.info(f"RFID switch monitoring started on GPIO {self.rfid_switch_pin}")

            # Initialize rotary encoder with callback using injected config
            self.encoder = RotaryEncoder(
                pin_a=self.config.ROTARY_ENCODER_PIN_A, 
                pin_b=self.config.ROTARY_ENCODER_PIN_B, 
                callback=self._on_rotate, 
                bouncetime=self.config.ENCODER_BOUNCETIME
            )

            # Initialize push buttons with callbacks using injected config
            self.button1 = PushButton(self.config.BUTTON_1_GPIO, callback=self._on_button1_press, bouncetime=self.config.BUTTON_BOUNCETIME)
            self.button2 = PushButton(self.config.BUTTON_2_GPIO, callback=self._on_button2_press, bouncetime=self.config.BUTTON_BOUNCETIME)
            self.button3 = PushButton(self.config.BUTTON_3_GPIO, callback=self._on_button3_press, bouncetime=self.config.BUTTON_BOUNCETIME)
            self.button5 = PushButton(self.config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=self.config.BUTTON_BOUNCETIME)

            logger.info("🔧 Hardware initialization complete")
            return self.display
            
        except Exception as e:
            logger.error(f"❌ Hardware initialization failed: {e}")
            logger.info("🖥️  Falling back to headless mode")
            from .devices.mock_display import MockDisplay
            return MockDisplay()

    def _on_rfid_switch_activated(self, channel):
        """Handle switch activation (card inserted) for RFID. Only trigger on actual FALLING edge (LOW)."""
        # Only proceed if the pin is actually LOW (FALLING edge)
        if not self.rfid_reader or not self.rfid_reader.initialized or self.rfid_reader.reading_active or GPIO.input(channel) != GPIO.LOW:
            return

        logger.info("🃏 Card insertion detected - starting RFID read...")
        # Use injected config instead of importing
        file_name = self.config.get_icon_path("contactless")
        context = {
            "title": f"Reading...",
            "icon_name": "contactless",
            "message": f"Reading album card",
            "background": "#24AC5F",
        }
        from app.ui.screens import MessageScreen
        try:
            logger.info("About to show MessageScreen for RFID read...")
            MessageScreen.show(context)
            logger.info("MessageScreen.show(context) completed successfully.")
        except Exception as e:
            logger.error(f"Exception in MessageScreen.show(context): {e}", exc_info=True)

        logger.info("Triggering RFID read due to switch activation")
        # Start reading and handle result in callback
        def rfid_result_callback(result):
            # Called from RFID reader thread when done
            _callback_result_status = result.get('status')
            logger.info(f"RFID read result: {_callback_result_status}")
            try:
                if _callback_result_status == "success":
                    # Let the normal new UID handler take over (already called by RC522Reader)
                    pass
                elif _callback_result_status == "timeout":
                    # Use injected config instead of importing
                    file_name = self.config.get_icon_path("error")
                    context = {
                        "title": f"Error Reading Card",
                        "icon_name": file_name,
                        "message": f"Reading timed out. Try again...",
                        "background": "#CCFF00",
                    }
                    from app.ui.screens import MessageScreen
                    MessageScreen.show(context)
                elif _callback_result_status == "error":
                    # Use injected config instead of importing
                    file_name = self.config.get_icon_path("library_music")
                    context = {
                        "title": f"Error Reading Card",
                        "icon_name": file_name,
                        "message": f"Try again...",
                        "background": "#FF0000",
                    }
                    from app.ui.screens import MessageScreen
                    MessageScreen.show(context)
            except Exception as e:
                logger.error(f"Exception in rfid_result_callback: {e}", exc_info=True)
        try:
            logger.info("About to call rfid_reader.start_reading...")
            self.rfid_reader.start_reading(result_callback=rfid_result_callback)
            logger.info("rfid_reader.start_reading returned (should be non-blocking)")
        except Exception as e:
            logger.error(f"Exception in rfid_reader.start_reading: {e}", exc_info=True)
    

    def _handle_new_uid(self, uid):
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.RFID_READ,
            payload={"rfid": uid}
        ))
        return
    
    def _on_button0_press(self):
        """Handle button 0 press - Generic button"""
        logger.info("Button 0 was pressed!")

        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 0, "action": "generic"}
        ))
    
    def _on_button1_press(self):
        """Handle button 1 press - Previous track"""
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 1, "action": "previous_track"}
        ))

    def _on_button2_press(self):
        """Handle button 2 press - Play/Pause"""
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 2, "action": "play_pause"}
        ))

    def _on_button3_press(self):
        """Handle button 3 press - Next track"""
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 3, "action": "next_track"}
        ))
    
    def _on_button4_press(self):
        """Handle button 4 press - TEMPORARILY DISABLED (used as NFC card switch)"""
        logger.info("Button 4 press detected")
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 4, "action": "stop"}
        ))
    
    def _on_button5_press(self):
        """Handle button 5 press - Rotary encoder button"""
        logger.info("Rotary encoder button was pressed!")
        # Use injected event_bus instead of importing
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": "rotary_encoder"}
        ))

    def _on_rotate(self, direction, position):
        """Handle rotary encoder rotation"""
        # Use injected event_bus instead of importing
        if direction > 0:
            self.event_bus.emit(Event(
                type=EventType.ROTARY_ENCODER,
                payload={"direction": "CW"}
            ))
        else:
            self.event_bus.emit(Event(
                type=EventType.ROTARY_ENCODER,
                payload={"direction": "CCW"}
            ))


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
