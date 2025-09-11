import RPi.GPIO as GPIO
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
        
        # Enhanced debouncing for KY-040
        self._lock = threading.Lock()
        self._last_encoded = 0
        self._encoder_value = 0
        self._last_time = 0
        self._min_interval = 0.01  # 10ms minimum interval between reads
        self._stable_reads = 3  # Number of consecutive stable reads required
        self._read_buffer = []
        
        # State tracking for proper quadrature decoding
        self._last_a = 0
        self._last_b = 0
        
        # Only disable warnings, don't cleanup all GPIO
        GPIO.setwarnings(False)
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Get initial state
            self._last_a = GPIO.input(self.pin_a)
            self._last_b = GPIO.input(self.pin_b)
            self._last_encoded = (self._last_a << 1) | self._last_b
            
            # Use shorter bouncetime and handle debouncing in software
            GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)
            GPIO.add_event_detect(self.pin_b, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)
            
            self.initialized = True
            logger.info(f"RotaryEncoder initialized on pins {pin_a}/{pin_b} with enhanced KY-040 debouncing")
            
        except RuntimeError as e:
            logger.error(f"Failed to initialize rotary encoder: {e}")
            logger.warning("Attempting to continue without rotary encoder functionality...")
            self.initialized = False

    def _update(self, channel):
        if not self.initialized:
            return
            
        current_time = time.time()
        
        # Minimum time interval check
        if current_time - self._last_time < self._min_interval:
            return
            
        with self._lock:
            try:
                # Read current state
                a = GPIO.input(self.pin_a)
                b = GPIO.input(self.pin_b)
                
                # Add to buffer for stability checking
                current_reading = (a << 1) | b
                self._read_buffer.append(current_reading)
                
                # Keep buffer size manageable
                if len(self._read_buffer) > self._stable_reads:
                    self._read_buffer.pop(0)
                
                # Check if we have enough stable readings
                if len(self._read_buffer) < self._stable_reads:
                    return
                    
                # Check if all readings in buffer are the same (stable)
                if not all(reading == self._read_buffer[0] for reading in self._read_buffer):
                    return
                
                # We have stable readings, process the change
                encoded = current_reading
                
                if encoded != self._last_encoded:
                    # Gray code / quadrature decoding for KY-040
                    direction = self._decode_rotation(encoded, self._last_encoded)
                    
                    if direction != 0:
                        self.position += direction
                        self._last_time = current_time
                        
                        if self.callback:
                            self.callback(direction, self.position)
                            
                        logger.debug(f"Encoder: direction={direction}, position={self.position}")
                
                self._last_encoded = encoded
                
            except Exception as e:
                logger.error(f"Error reading rotary encoder: {e}")

    def _decode_rotation(self, encoded, last_encoded):
        """
        Decode KY-040 quadrature signals using gray code sequence.
        Returns: 1 for clockwise, -1 for counter-clockwise, 0 for no movement
        """
        # KY-040 Gray code sequence (clockwise): 00 -> 01 -> 11 -> 10 -> 00
        transition_table = {
            (0b00, 0b01): 1,   # 00 -> 01 = CW
            (0b01, 0b11): 1,   # 01 -> 11 = CW  
            (0b11, 0b10): 1,   # 11 -> 10 = CW
            (0b10, 0b00): 1,   # 10 -> 00 = CW
            
            (0b01, 0b00): -1,  # 01 -> 00 = CCW
            (0b11, 0b01): -1,  # 11 -> 01 = CCW
            (0b10, 0b11): -1,  # 10 -> 11 = CCW
            (0b00, 0b10): -1,  # 00 -> 10 = CCW
        }
        
        transition = (last_encoded, encoded)
        return transition_table.get(transition, 0)

    def get_position(self):
        return self.position

    def cleanup(self):
        try:
            # Check if GPIO is still in a valid state
            if GPIO.getmode() is not None:
                GPIO.remove_event_detect(self.pin_a)
                GPIO.remove_event_detect(self.pin_b)
        except Exception as e:
            logger.error(f"Encoder cleanup error: {e}")
