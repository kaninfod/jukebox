import RPi.GPIO as GPIO
import threading
import time

class PushButton:
    def __init__(self, pin, callback=None, bouncetime=200):
        self.pin = pin
        self.callback = callback
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._handle_press, bouncetime=bouncetime)

    def _handle_press(self, channel):
        print(f"Button on GPIO {self.pin} pressed!")
        if self.callback:
            self.callback()

    def cleanup(self):
        GPIO.remove_event_detect(self.pin)
