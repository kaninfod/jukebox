import logging
import RPi.GPIO as GPIO
import threading
import time

logger = logging.getLogger(__name__)

class PushButton:
    def __init__(self, pin, callback=None, bouncetime=200):
        self.pin = pin
        self.callback = callback
        
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.pin,
                GPIO.FALLING,
                callback=self._handle_press,
                bouncetime=200
            )
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize button on GPIO {self.pin}: {e}")
            logger.warning(f"Attempting to continue without button {self.pin} functionality...")
            self.initialized = False

        if self.initialized:
            logger.info(f"PushButton initialized on GPIO {self.pin}")

    def _handle_press(self, channel):
        if not self.initialized:
            return
        logger.info(f"Button on GPIO {self.pin} pressed!")
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error in button callback: {e}")

    def cleanup(self):
        if not self.initialized:
            return
        try:
            GPIO.cleanup(self.pin)
        except Exception as e:
            logger.error(f"Button GPIO cleanup error: {e}")
