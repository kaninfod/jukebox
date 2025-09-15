
"""
Hardware management module for the jukebox.
Handles initialization and callbacks for all hardware devices.
"""
import pigpio

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
        if not self.config.HARDWARE_MODE:
            logger.info("🖥️  Headless mode enabled - skipping hardware initialization")
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

            # Set up switch pin for RFID using pigpio
            self.rfid_switch_pin = self.config.NFC_CARD_SWITCH_GPIO
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpio daemon")
            self.pi.set_mode(self.rfid_switch_pin, pigpio.INPUT)
            self.pi.set_pull_up_down(self.rfid_switch_pin, pigpio.PUD_UP)
            self.rfid_cb = self.pi.callback(self.rfid_switch_pin, pigpio.FALLING_EDGE, self._on_rfid_switch_activated)
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
            self.button4 = PushButton(self.config.BUTTON_4_GPIO, callback=self._on_button4_press, bouncetime=self.config.BUTTON_BOUNCETIME)
            self.button5 = PushButton(self.config.BUTTON_5_GPIO, callback=self._on_button5_press, bouncetime=self.config.BUTTON_BOUNCETIME)

            logger.info("🔧 Hardware initialization complete")
            return self.display
            
        except Exception as e:
            logger.error(f"❌ Hardware initialization failed: {e}")
            logger.info("🖥️  Falling back to headless mode")
            from .devices.mock_display import MockDisplay
            return MockDisplay()

    def _on_rfid_switch_activated(self, gpio, level, tick):
        """Handle switch activation (card inserted) for RFID. Only trigger on actual FALLING edge (LOW)."""
        logger.info(f"RFID switch callback fired: gpio={gpio}, level={level}, tick={tick}, initialized={getattr(self.rfid_reader, 'initialized', None)}, reading_active={getattr(self.rfid_reader, 'reading_active', None)}")
        # Only proceed if the pin is actually LOW (FALLING edge)
        if not self.rfid_reader or not self.rfid_reader.initialized or self.rfid_reader.reading_active or level != 0:
            logger.debug("RFID switch callback blocked by state check.")
            return

        logger.info("🃏 Card insertion detected - starting RFID read...")
        # Use injected config instead of importing
        from app.core import event_bus, EventType, Event
        event = Event(EventType.SHOW_SCREEN_QUEUED,
            payload={
                "screen_type": "message",
                "context": {
                    "title": "Reading...",
                    "icon_name": "contactless",
                    "message": "Reading album card",
                    "theme": "message_info"
                },
                "duration": 3
            }
        )
        event_bus.emit(event)



        # from app.core.event_factory import EventFactory
        # from app.core import event_bus
        
        # event = EventFactory.show_screen_queued( #EventFactory.show_screen_queued(
        #     screen_type="message",
        #     context={
        #         "title": "Reading...",
        #         "icon_name": "contactless",
        #         "message": "Reading album card",
        #         "theme": "message_info"
        #     },
        #     duration=5.0
        # )
        # event_bus.emit(event)

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
                    from app.core import event_bus, EventType, Event
                    event = Event(EventType.SHOW_SCREEN_QUEUED,
                        payload={
                            "screen_type": "message",
                            "context": {
                                "title": "Error Reading Card",
                                "icon_name": "error",
                                "message": "Reading timed out. Try again...",
                                "theme": "message_info"
                            },
                            "duration": 3
                        }
                    )
                    event_bus.emit(event)


                    # from app.core.event_factory import EventFactory
                    # from app.core import event_bus
                    
                    # event = EventFactory.show_screen_queued( #EventFactory.show_screen_queued(
                    #     screen_type="message",
                    #     context={
                    #         "title": "Error Reading Card",
                    #         "icon_name": "error",
                    #         "message": "Reading timed out. Try again...",
                    #         "theme": "message_info"
                    #     },
                    #     duration=5.0
                    # )
                    # event_bus.emit(event)

                elif _callback_result_status == "error":
                    #from app.core.event_factory import EventFactory
                    from app.core import event_bus, EventType, Event
                    event = Event(EventType.SHOW_SCREEN_QUEUED,
                        payload={
                            "screen_type": "message",
                            "context": {
                                "title": "Error Reading Card",
                                "icon_name": "error",
                                "message": "Try again...",
                                "theme": "message_info"},
                            "duration": 3
                        }
                    )
                    event_bus.emit(event)

                    # event = EventFactory.show_screen_queued( 
                    #     screen_type="message",
                    #     context={
                    #         "title": "Error Reading Card",
                    #         "icon_name": "error",
                    #         "message": "Try again...",
                    #         "theme": "message_info"
                    #     },
                    #     duration=5.0
                    # )
                    # event_bus.emit(event)

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
        """Handle button 4 press - Stop"""
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
        if hasattr(self, 'rfid_cb'):
            try:
                self.rfid_cb.cancel()
                logger.info(f"RFID switch pigpio callback cancelled for GPIO {self.rfid_switch_pin}")
            except Exception as e:
                logger.error(f"Error cancelling RFID switch pigpio callback: {e}")
        if hasattr(self, 'pi'):
            try:
                self.pi.stop()
            except Exception as e:
                logger.error(f"Error stopping pigpio instance: {e}")
                
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
