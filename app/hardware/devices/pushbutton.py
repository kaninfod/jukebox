import logging
import board
import keypad
import threading
import time

logger = logging.getLogger(__name__)


class PushButton:
    """
    PushButton using CircuitPython keypad module for event-driven button handling.
    Supports press (immediate), short press (on release), and long press callbacks.
    """
    def __init__(self, pin, callback=None, press_callback=None, long_press_callback=None, long_press_threshold=3.0, bouncetime=200, pull_up_down=True):
        self.pin = pin
        self.callback = callback  # Fires on release (short press)
        self.press_callback = press_callback  # Fires immediately on press
        self.long_press_callback = long_press_callback
        self.long_press_threshold = long_press_threshold
        self._press_time = None
        self._monitor_thread = None
        self._running = False

        try:
            # Convert BCM pin number to board pin
            board_pin = self._bcm_to_board_pin(pin)
            
            # Create keypad.Keys object for this single button
            # value_when_pressed=False: button connects GPIO to GND
            # pull=True: enable internal pull-up resistor
            self.key = keypad.Keys(
                pins=(board_pin,),
                value_when_pressed=False,
                pull=pull_up_down,
                interval=bouncetime / 1000.0  # Convert milliseconds to seconds
            )
            
            self.initialized = True
            logger.info(f"PushButton initialized on GPIO {self.pin} using CircuitPython keypad")
            
            # Start monitoring thread
            self._running = True
            self._monitor_thread = threading.Thread(target=self._event_loop, daemon=True)
            self._monitor_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to initialize button on GPIO {self.pin}: {e}")
            logger.warning(f"Attempting to continue without button {self.pin} functionality...")
            self.initialized = False

    def _bcm_to_board_pin(self, bcm_pin):
        """Convert BCM GPIO number to board.D pin."""
        # BCM to board.D mapping for Raspberry Pi
        bcm_map = {
            4: board.D4, 5: board.D5, 6: board.D6, 7: board.D7,
            8: board.D8, 9: board.D9, 10: board.D10, 11: board.D11,
            12: board.D12, 13: board.D13, 14: board.D14, 15: board.D15,
            16: board.D16, 17: board.D17, 18: board.D18, 19: board.D19,
            20: board.D20, 21: board.D21, 22: board.D22, 23: board.D23,
            24: board.D24, 25: board.D25, 26: board.D26, 27: board.D27,
        }
        return bcm_map[bcm_pin]

    def _event_loop(self):
        """Event loop that monitors button press/release events."""
        while self._running and self.initialized:
            event = self.key.events.get()
            if event:
                if event.pressed:
                    # Button pressed - record the time and fire press callback
                    self._press_time = time.monotonic()
                    logger.debug(f"Button on GPIO {self.pin} pressed")
                    
                    # Fire immediate press callback (for microswitches, etc.)
                    if self.press_callback:
                        try:
                            self.press_callback()
                        except Exception as e:
                            logger.error(f"Error in press callback: {e}")
                    
                elif event.released:
                    # Button released - determine if short or long press
                    if self._press_time is not None:
                        press_duration = time.monotonic() - self._press_time
                        
                        if press_duration >= self.long_press_threshold:
                            # Long press detected
                            if self.long_press_callback:
                                logger.info(f"Button on GPIO {self.pin} long pressed! ({press_duration:.2f}s)")
                                try:
                                    self.long_press_callback()
                                except Exception as e:
                                    logger.error(f"Error in long press callback: {e}")
                        else:
                            # Short press detected
                            if self.callback:
                                logger.info(f"Button on GPIO {self.pin} short pressed! ({press_duration:.2f}s)")
                                try:
                                    self.callback()
                                except Exception as e:
                                    logger.error(f"Error in button callback: {e}")
                        
                        self._press_time = None
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.01)

    def cleanup(self):
        """Stop the event loop and clean up resources."""
        if not self.initialized:
            return
        try:
            self._running = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)
            self.key.deinit()
            logger.info(f"Button on GPIO {self.pin} cleaned up")
        except Exception as e:
            logger.error(f"Button GPIO cleanup error: {e}")
