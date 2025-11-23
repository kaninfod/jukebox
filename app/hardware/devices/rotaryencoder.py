import board
#import rotaryio
from ruhrohrotaryio import IncrementalEncoder as rotaryio_IncrementalEncoder
import threading
import time
import logging

logger = logging.getLogger(__name__)

class RotaryEncoder:
    """
    Rotary encoder using CircuitPython rotaryio module for hardware quadrature decoding.
    The rotaryio.IncrementalEncoder handles all the quadrature state machine logic in hardware.
    We just poll for position changes and fire callbacks.
    """
    def __init__(self, pin_a, pin_b, callback=None, bouncetime=5):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.callback = callback
        self.last_position = 0
        self._last_callback_time = 0
        self._min_callback_interval = 0.15  # 150ms minimum between callbacks (aggressive filtering for jittery encoder)
        
        self._monitor_thread = None
        self._running = False
        
        try:
            # Convert BCM pin numbers to board pins
            board_pin_a = self._bcm_to_board_pin(pin_a)
            board_pin_b = self._bcm_to_board_pin(pin_b)
            
            # Create IncrementalEncoder - handles quadrature decoding in hardware
            # divisor=4 means we get one count per detent click on KY-040
            #self.encoder = rotaryio.IncrementalEncoder(board_pin_a, board_pin_b, divisor=4)
            
            self.encoder = rotaryio_IncrementalEncoder(board_pin_a, board_pin_b, divisor=4)


            self.initialized = True
            logger.info(f"RotaryEncoder initialized on GPIO {self.pin_a}/{self.pin_b} using CircuitPython rotaryio")
            
            # Start monitoring thread to poll for position changes
            self._running = True
            self._monitor_thread = threading.Thread(target=self._poll_position, daemon=True)
            self._monitor_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to initialize rotary encoder: {e}")
            logger.warning("Attempting to continue without rotary encoder functionality...")
            self.initialized = False

    def _bcm_to_board_pin(self, bcm_pin):
        """Convert BCM GPIO number to board.D pin."""
        bcm_map = {
            4: board.D4, 5: board.D5, 6: board.D6, 7: board.D7,
            8: board.D8, 9: board.D9, 10: board.D10, 11: board.D11,
            12: board.D12, 13: board.D13, 14: board.D14, 15: board.D15,
            16: board.D16, 17: board.D17, 18: board.D18, 19: board.D19,
            20: board.D20, 21: board.D21, 22: board.D22, 23: board.D23,
            24: board.D24, 25: board.D25, 26: board.D26, 27: board.D27,
        }
        return bcm_map[bcm_pin]

    def _poll_position(self):
        """Poll the encoder position and fire callback when it changes."""
        while self._running and self.initialized:
            try:
                current_position = self.encoder.position
                if current_position != self.last_position:
                    # Calculate direction first (before any filtering)
                    # Positive change = CW (turning right), Negative change = CCW (turning left)
                    if current_position > self.last_position:
                        direction = 1  # Clockwise (volume up)
                    else:
                        direction = -1  # Counter-clockwise (volume down)
                    
                    # Update last_position immediately to track actual encoder state
                    self.last_position = current_position
                    
                    # Apply hysteresis: only fire callback if enough time has passed
                    current_time = time.monotonic()
                    if current_time - self._last_callback_time < self._min_callback_interval:
                        # Too soon since last callback - ignore this change (jitter/bounce)
                        logger.debug(f"Encoder jitter ignored: position={current_position}, direction={direction} (within {self._min_callback_interval}s)")
                        continue
                    
                    logger.debug(f"Encoder position changed: {self.last_position - direction} -> {current_position}, direction={direction}")
                    
                    if self.callback:
                        self.callback(direction, current_position)
                        self._last_callback_time = current_time
                    
            except Exception as e:
                logger.error(f"Error reading rotary encoder: {e}")
            
            time.sleep(0.01)  # Poll every 10ms

    def get_position(self):
        """Get the current encoder position."""
        return self.encoder.position if self.initialized else 0

    def cleanup(self):
        """Stop the polling thread and clean up resources."""
        if not self.initialized:
            return
        try:
            self._running = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)
            self.encoder.deinit()
            logger.info(f"RotaryEncoder on GPIO {self.pin_a}/{self.pin_b} cleaned up")
        except Exception as e:
            logger.error(f"Encoder cleanup error: {e}")
