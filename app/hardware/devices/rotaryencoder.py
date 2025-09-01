import RPi.GPIO as GPIO
import threading
import time
import logging

logger = logging.getLogger(__name__)

class RotaryEncoder:
    def __init__(self, pin_a, pin_b, callback=None, bouncetime=2):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.callback = callback
        self.position = 0
        self.last_state = None
        self._lock = threading.Lock()
        
        # Only disable warnings, don't cleanup all GPIO
        GPIO.setwarnings(False)
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)
            GPIO.add_event_detect(self.pin_b, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)
            self.initialized = True
        except RuntimeError as e:
            logger.error(f"Failed to initialize rotary encoder: {e}")
            logger.warning("Attempting to continue without rotary encoder functionality...")
            self.initialized = False

    def _update(self, channel):
        if not self.initialized:
            return
            
        with self._lock:
            try:
                a = GPIO.input(self.pin_a)
                b = GPIO.input(self.pin_b)
                state = (a, b)
                if self.last_state is None:
                    self.last_state = state
                    return
                # Only act on full detent (both high)
                if state == (1, 1) and self.last_state != (1, 1):
                    # Determine direction by which pin triggered the event
                    if channel == self.pin_a:
                        # Pin A triggered first, clockwise
                        self.position += 1
                        direction = 1
                    else:
                        # Pin B triggered first, counter-clockwise  
                        self.position -= 1
                        direction = -1
                    
                    if self.callback:
                        self.callback(direction, self.position)
                
                self.last_state = state
            except Exception as e:
                logger.error(f"Error reading rotary encoder: {e}")

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
