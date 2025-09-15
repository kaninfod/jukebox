import logging
import pigpio
import threading
import time

logger = logging.getLogger(__name__)

class PushButton:
    def __init__(self, pin, callback=None, bouncetime=200):
        self.pin = pin
        self.callback = callback
        
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpio daemon")
            self.pi.set_mode(self.pin, pigpio.INPUT)
            self.pi.set_pull_up_down(self.pin, pigpio.PUD_UP)
            # Register callback for falling edge
            self.callback_obj = self.pi.callback(self.pin, pigpio.FALLING_EDGE, self._handle_press)
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize button on GPIO {self.pin}: {e}")
            logger.warning(f"Attempting to continue without button {self.pin} functionality...")
            self.initialized = False

        if self.initialized:
            logger.info(f"PushButton initialized on GPIO {self.pin}")

    def _handle_press(self, gpio, level, tick):
        if not self.initialized:
            return
        if level == 0:  # FALLING_EDGE
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
            if hasattr(self, 'callback_obj'):
                self.callback_obj.cancel()
            if hasattr(self, 'pi'):
                self.pi.stop()
        except Exception as e:
            logger.error(f"Button GPIO cleanup error: {e}")
