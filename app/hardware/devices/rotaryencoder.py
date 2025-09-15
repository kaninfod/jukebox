import pigpio
import threading
import time
import logging

logger = logging.getLogger(__name__)

class RotaryEncoder:
    def __init__(self, pin_a, pin_b, callback=None, bouncetime=5):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.callback = callback
        self.position = 0
        
        # Detent-based counting for KY-040 (only count complete clicks)
        self._lock = threading.Lock()
        self._last_time = 0
        self._min_interval = 0.002  # 2ms minimum interval
        
        # State tracking for detent detection with hysteresis
        self._last_encoded = 0
        self._detent_state = 0b11  # KY-040 rests at 11 (both high)
        self._sequence_history = []  # Track state sequence for hysteresis
        self._confirmed_direction = 0  # Only count when we have a confirmed direction
        
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpio daemon")
            self.pi.set_mode(self.pin_a, pigpio.INPUT)
            self.pi.set_pull_up_down(self.pin_a, pigpio.PUD_UP)
            self.pi.set_mode(self.pin_b, pigpio.INPUT)
            self.pi.set_pull_up_down(self.pin_b, pigpio.PUD_UP)
            # Get initial state - KY-040 should rest at 11
            a = self.pi.read(self.pin_a)
            b = self.pi.read(self.pin_b)
            self._last_encoded = (a << 1) | b
            # Register callbacks for both pins
            self.cb_a = self.pi.callback(self.pin_a, pigpio.EITHER_EDGE, self._update)
            self.cb_b = self.pi.callback(self.pin_b, pigpio.EITHER_EDGE, self._update)
            self.initialized = True
            logger.info(f"RotaryEncoder initialized on pins {self.pin_a}/{self.pin_b} for KY-040 detent counting")
        except Exception as e:
            logger.error(f"Failed to initialize rotary encoder: {e}")
            logger.warning("Attempting to continue without rotary encoder functionality...")
            self.initialized = False

    def _update(self, gpio, level, tick):
        if not self.initialized:
            return
        current_time = time.time()
        # Time-based debouncing
        if current_time - self._last_time < self._min_interval:
            return
        with self._lock:
            try:
                # Read current state
                a = self.pi.read(self.pin_a)
                b = self.pi.read(self.pin_b)
                encoded = (a << 1) | b
                # Only process if state changed
                if encoded != self._last_encoded:
                    # Add to sequence history for hysteresis
                    self._sequence_history.append(encoded)
                    # Keep only recent history (last 4 states)
                    if len(self._sequence_history) > 4:
                        self._sequence_history.pop(0)
                    # Check for complete detent sequence with hysteresis
                    if encoded == self._detent_state and self._last_encoded != self._detent_state:
                        # We've returned to detent position - validate we had a complete sequence
                        direction = self._is_valid_detent_sequence()
                        if direction != 0:
                            self.position += direction
                            self._last_time = current_time
                            if self.callback:
                                self.callback(direction, self.position)
                            logger.debug(f"Confirmed detent: direction={direction}, position={self.position}, sequence={self._sequence_history}")
                        # Clear history after detent detection
                        self._sequence_history = [encoded]
                self._last_encoded = encoded
            except Exception as e:
                logger.error(f"Error reading rotary encoder: {e}")

    def _is_valid_detent_sequence(self):
        """
        Validate that we have a complete encoder sequence with strict requirements.
        Requires complete 4-5 state sequences to prevent partial movement detection.
        
        Valid KY-040 complete sequences only:
        Clockwise: 11 -> 01 -> 00 -> 10 -> 11 (full sequence)
        Counter-clockwise: 11 -> 10 -> 00 -> 01 -> 11 (full sequence)
        
        Partial sequences like [3,1,3] or [3,2,3] are rejected as incomplete movements.
        """
        if len(self._sequence_history) < 4:
            logger.debug(f"Sequence too short for validation (need >=4): {self._sequence_history}")
            return 0
            
        # Look for complete 4-5 state patterns only
        sequence = self._sequence_history[-5:] if len(self._sequence_history) >= 5 else self._sequence_history[-4:]
        
        # Complete clockwise sequences (4-5 states)
        if len(sequence) >= 4:
            # Full clockwise: 11 -> 01 -> 00 -> 10 -> 11 or 01 -> 00 -> 10 -> 11
            if (sequence == [0b11, 0b01, 0b00, 0b10] or 
                sequence == [0b01, 0b00, 0b10, 0b11] or
                (len(sequence) >= 5 and sequence[-5:] == [0b11, 0b01, 0b00, 0b10, 0b11])):
                logger.debug(f"Complete clockwise sequence detected: {sequence}")
                return -1
                
        # Complete counter-clockwise sequences (4-5 states)  
        if len(sequence) >= 4:
            # Full counter-clockwise: 11 -> 10 -> 00 -> 01 -> 11 or 10 -> 00 -> 01 -> 11
            if (sequence == [0b11, 0b10, 0b00, 0b01] or 
                sequence == [0b10, 0b00, 0b01, 0b11] or
                (len(sequence) >= 5 and sequence[-5:] == [0b11, 0b10, 0b00, 0b01, 0b11])):
                logger.debug(f"Complete counter-clockwise sequence detected: {sequence}")
                return 1
        
        # Reject all partial sequences (including [3,1,3] and [3,2,3] patterns)
        logger.debug(f"Incomplete/partial sequence rejected: {sequence}")
        return 0

    def get_position(self):
        return self.position

    def cleanup(self):
        try:
            if hasattr(self, 'cb_a'):
                self.cb_a.cancel()
            if hasattr(self, 'cb_b'):
                self.cb_b.cancel()
            if hasattr(self, 'pi'):
                self.pi.stop()
        except Exception as e:
            logger.error(f"Encoder cleanup error: {e}")
