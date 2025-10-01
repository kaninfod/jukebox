import logging
import RPi.GPIO as GPIO
import threading
import time

logger = logging.getLogger(__name__)


class PushButton:
    def __init__(self, pin, callback=None, long_press_callback=None, long_press_threshold=3.0, bouncetime=200, pull_up_down=GPIO.PUD_UP):
        self.pin = pin
        self.callback = callback
        self.long_press_callback = long_press_callback
        self.long_press_threshold = long_press_threshold
        self._press_time = None
        self._press_timer = None
        self._pressed = False

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            if pull_up_down is not None:
                GPIO.setup(self.pin, GPIO.IN, pull_up_down=pull_up_down)
            else:
                GPIO.setup(self.pin, GPIO.IN)
            GPIO.add_event_detect(
                self.pin,
                GPIO.FALLING,
                callback=self._handle_press,
                bouncetime=bouncetime
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
        # Start a thread to monitor for long press
        if not self._pressed:
            self._pressed = True
            self._press_time = time.monotonic()
            self._press_timer = threading.Thread(target=self._monitor_press)
            self._press_timer.daemon = True
            self._press_timer.start()

    def _monitor_press(self):
        # Wait for button release or long press threshold
        while GPIO.input(self.pin) == GPIO.LOW:
            if (time.monotonic() - self._press_time) >= self.long_press_threshold:
                if self.long_press_callback:
                    logger.info(f"Button on GPIO {self.pin} long pressed!")
                    try:
                        self.long_press_callback()
                    except Exception as e:
                        logger.error(f"Error in long press callback: {e}")
                # Wait for release to avoid duplicate events
                while GPIO.input(self.pin) == GPIO.LOW:
                    time.sleep(0.01)
                self._pressed = False
                return
            time.sleep(0.01)
        # If released before threshold, treat as normal press
        if self.callback:
            logger.info(f"Button on GPIO {self.pin} short pressed!")
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error in button callback: {e}")
        self._pressed = False

    def cleanup(self):
        if not self.initialized:
            return
        try:
            GPIO.cleanup(self.pin)
        except Exception as e:
            logger.error(f"Button GPIO cleanup error: {e}")
