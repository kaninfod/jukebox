import RPi.GPIO as GPIO
import threading
import time

class RotaryEncoder:
    def __init__(self, pin_a, pin_b, callback=None, bouncetime=2):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.callback = callback
        self.position = 0
        self.last_state = None
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._lock = threading.Lock()
        GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)
        GPIO.add_event_detect(self.pin_b, GPIO.BOTH, callback=self._update, bouncetime=bouncetime)

    def _update(self, channel):
        with self._lock:
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
                    self.position += 1
                    direction = 1
                else:
                    self.position -= 1
                    direction = -1
                if self.callback:
                    self.callback(self.position, direction)
            self.last_state = state

    def get_position(self):
        return self.position

    def cleanup(self):
        GPIO.remove_event_detect(self.pin_a)
        GPIO.remove_event_detect(self.pin_b)
