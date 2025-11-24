"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
#from .devices.ili9488 import ILI9488
#from .devices.rfid import RC522Reader
from .devices.pushbutton import PushButton
from .devices.rotaryencoder import RotaryEncoder
import logging
from app.core import EventType, Event

logger = logging.getLogger(__name__)

class HardwareManager:
    
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
        #self.screen_manager = screen_manager
        self.playback_service = None
        
        # Hardware device instances
        self.display = None
        self.rfid_reader = None
        self.rfid_switch = None
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
        if not self.config.HARDWARE_MODE:
            logger.info("🖥️  Headless mode enabled - skipping hardware initialization")
            from .devices.mock_display import MockDisplay
            return MockDisplay()
        
        try:
            # Initialize display
            
            from .devices.mock_display import MockDisplay
            #return MockDisplay()
            self.display = MockDisplay()


            from .devices.pn532_rfid import PN532Reader
            self.rfid_reader = PN532Reader

            # Set up RFID microswitch using CircuitPython PushButton
            # Card insertion triggers press_callback immediately (not on release)
            self.rfid_switch = PushButton(
                pin=self.config.NFC_CARD_SWITCH_GPIO,
                press_callback=self._on_rfid_switch_activated,  # Fire on press, not release
                bouncetime=200,
                pull_up_down=True  # Enable internal pull-up resistor
            )

            # Initialize rotary encoder with callback using CircuitPython keypad
            self.encoder = RotaryEncoder(
                pin_a=self.config.ROTARY_ENCODER_PIN_A,
                pin_b=self.config.ROTARY_ENCODER_PIN_B,
                callback=self._on_rotate,
                bouncetime=self.config.ENCODER_BOUNCETIME
            )

            # Initialize push buttons with callbacks using injected config
            self.button1 = PushButton(self.config.BUTTON_1_GPIO, callback=self._on_button1_press, bouncetime=self.config.BUTTON_BOUNCETIME, pull_up_down=None)
            self.button2 = PushButton(self.config.BUTTON_2_GPIO, callback=self._on_button2_press, bouncetime=self.config.BUTTON_BOUNCETIME, pull_up_down=None)
            self.button3 = PushButton(self.config.BUTTON_3_GPIO, callback=self._on_button3_press, bouncetime=self.config.BUTTON_BOUNCETIME, pull_up_down=None)
            self.button4 = PushButton(
                self.config.BUTTON_4_GPIO,
                callback=self._on_button4_press,
                long_press_callback=self._on_button4_long_press,
                long_press_threshold=5,
                bouncetime=self.config.BUTTON_BOUNCETIME
            )
            self.button5 = PushButton(self.config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=self.config.BUTTON_BOUNCETIME)

            logger.info("🔧 Hardware initialization complete")
            return self.display
            
        except Exception as e:
            logger.error(f"❌ Hardware initialization failed: {e}")
            # logger.info("🖥️  Falling back to headless mode")
            # from .devices.mock_display import MockDisplay
            # return MockDisplay()


    def _on_rfid_switch_activated(self):
        """Handle switch activation (card inserted) for RFID. Triggered by CircuitPython keypad event."""
        logger.info("🃏 RFID switch activated - card detected")
        
        from app.core.service_container import get_service
        playback_service = get_service("playback_service")
        encoding_mode = playback_service.is_encoding_mode_active()
        logger.debug(f"Encoding_mode={encoding_mode}")
        if encoding_mode:    
            try:
                from app.services.nfc_encoding_session import nfc_encoding_session
            except ImportError:
                nfc_encoding_session = None
            if not nfc_encoding_session:
                logger.error("NFC Encoding session service not available.")
                return False
            if nfc_encoding_session.active:
                album_id = nfc_encoding_session.album_id
                data = {"album_id": album_id}
                reader = self.rfid_reader()
                result = reader.write_data(data, result_callback=self._rfid_write_callback)
                logger.info("PN532Reader.write_data returned (one-shot)")

        else:
            logger.info("🃏 Card insertion detected - starting PN532 read (one-shot)...")
            from app.core import event_bus, EventType, Event
            event = Event(EventType.SHOW_SCREEN_QUEUED,
                payload={
                    "screen_type": "message",
                    "context": {
                        "title": "Reading...",
                        "icon_name": "contactless.png",
                        "message": "Reading album card",
                        "theme": "message_info"
                    },
                    "duration": 3
                }
            )
            event_bus.emit(event)

            logger.info("Triggering PN532 read due to switch activation")
            try:
                logger.info("About to instantiate and call PN532Reader.start_reading...")
                reader = self.rfid_reader()
                # Use lambda to pass encoding_mode and playback_service
                reader.start_reading(result_callback= self._rfid_read_callback)
                logger.info("PN532Reader.start_reading returned (one-shot)")
            except Exception as e:
                logger.error(f"Exception in PN532Reader.start_reading: {e}", exc_info=True)

    def _rfid_write_callback(self, result):
        logger.info(f"RFID write result: {result}")
        uid = result.get('uid')
        album_id = result.get('blocks', {}).get('album_id')
        from app.core import event_bus, EventType, Event
        self.event_bus.emit(Event(
            type=EventType.ENCODE_CARD,
            payload={"rfid": uid, "album_id": album_id}
        ))



    def _rfid_read_callback(self, result):
        """Callback function to handle RFID read results from PN532Reader."""
        from app.core import event_bus, EventType, Event

        _callback_result_status = result.get('status')
        logger.info(f"RFID read result: {_callback_result_status}")
        try:
            if _callback_result_status == "success":
                uid = result.get('uid')
                album_id = result.get('blocks', {}).get('album_id')
                from app.core import event_bus, EventType, Event
                self.event_bus.emit(Event(
                    type=EventType.RFID_READ,
                    payload={"rfid": uid, "album_id": album_id}
                ))

            elif _callback_result_status == "timeout":
                event = Event(EventType.SHOW_SCREEN_QUEUED,
                    payload={
                        "screen_type": "message",
                        "context": {
                            "title": "Error Reading Card",
                            "icon_name": "error.png",
                            "message": "Reading timed out. Try again...",
                            "theme": "message_info"
                        },
                        "duration": 3
                    }
                )
                event_bus.emit(event)
            elif _callback_result_status == "error":
                event = Event(EventType.SHOW_SCREEN_QUEUED,
                    payload={
                        "screen_type": "message",
                        "context": {
                            "title": "Error Reading Card",
                            "icon_name": "error.png",
                            "message": "Try again...",
                            "theme": "message_info"},
                        "duration": 3
                    }
                )
                event_bus.emit(event)
        except Exception as e:
            logger.error(f"Exception in rfid_result_callback: {e}", exc_info=True)



    def _on_button0_press(self):
        """Handle button 0 press - Generic button"""
        logger.info("Button 0 was pressed!")
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 0, "action": "generic"}
        ))
    
    def _on_button1_press(self):
        """Handle button 1 press - Previous track"""
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 1, "action": "previous_track"}
        ))

    def _on_button2_press(self):
        """Handle button 2 press - Play/Pause"""
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 2, "action": "play_pause"}
        ))

    def _on_button3_press(self):
        """Handle button 3 press - Next track"""
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 3, "action": "next_track"}
        ))
    
    def _on_button4_press(self):
        """Handle button 4 press - Stop"""
        logger.info("Button 4 press detected")
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": 4, "action": "stop"}
        ))
    
    def _on_button4_long_press(self):
        """Handle button 4 long press - System Reboot"""
        logger.info("Button 4 long press detected (requesting system reboot)")
        self.event_bus.emit(Event(
            type=EventType.SYSTEM_REBOOT_REQUESTED,
            payload={"button": 4}
        ))

    def _on_button5_press(self):
        """Handle button 5 press - Rotary encoder button"""
        logger.info("Rotary encoder button was pressed!")
        self.event_bus.emit(Event(
            type=EventType.BUTTON_PRESSED,
            payload={"button": "rotary_encoder"}
        ))

    def _on_rotate(self, direction, position):
        """
        Handle rotary encoder rotation.
        direction=1 means CW (position increased), direction=-1 means CCW (position decreased)
        """
        if direction > 0:
            # Clockwise rotation (turning right = volume up)
            self.event_bus.emit(Event(
                type=EventType.ROTARY_ENCODER,
                payload={"direction": "CW"}
            ))
        else:
            # Counter-clockwise rotation (turning left = volume down)
            self.event_bus.emit(Event(
                type=EventType.ROTARY_ENCODER,
                payload={"direction": "CCW"}
            ))


    def cleanup(self):
        """Clean up GPIO resources"""
        # Clean up individual devices first (while GPIO mode is still set)               
        if self.rfid_reader:
            try:
                pass
                #self.rfid_reader.stop()
            except Exception as e:
                logger.error(f"RFID cleanup error: {e}")
        # Clean up RFID switch (CircuitPython PushButton)
        if self.rfid_switch:
            try:
                self.rfid_switch.cleanup()
            except Exception as e:
                logger.error(f"RFID switch cleanup error: {e}")
                
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
        
        # No final GPIO cleanup needed for lgpio


# import RPi.GPIO as GPIO
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# print(GPIO.input(26))