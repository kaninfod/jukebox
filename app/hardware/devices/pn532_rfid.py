import threading
import time
import logging
from digitalio import DigitalInOut
import board
import busio
from adafruit_pn532.spi import PN532_SPI

logger = logging.getLogger(__name__)

class PN532Reader:
    def __init__(self, cs_pin=7, on_new_uid=None):
        """
        Initialize PN532 RFID reader with switch-triggered reading.
        Args:
            cs_pin: GPIO pin for PN532 CS (default: 7)
            on_new_uid: Callback function called when new UID is detected
        """
        self.cs_pin = cs_pin
        self.on_new_uid = on_new_uid
        self.pn532 = None
        self.initialized = False
        self.reading_active = False
        self.read_thread = None
        self.stop_reading = False
        self._result_callback = None
        try:
            spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            cs = DigitalInOut(getattr(board, f"D{self.cs_pin}"))
            self.pn532 = PN532_SPI(spi, cs, debug=False)
            self.pn532.SAM_configuration()
            self.initialized = True
            logger.info("PN532 RFID reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PN532 reader: {e}")
            self.initialized = False

    def start_reading(self, result_callback=None):
        logger.debug(f"start_reading called. initialized={self.initialized}, reading_active={self.reading_active}")
        if not self.initialized:
            logger.error("PN532 reader not initialized, cannot start reading")
            return False
        if self.reading_active:
            logger.warning("PN532 reading already in progress")
            return False
        self.reading_active = True
        self.stop_reading = False
        self._result_callback = result_callback
        self.read_thread = threading.Thread(target=self._read_with_timeout, daemon=True)
        self.read_thread.start()
        return True

    def _read_with_timeout(self):
        start_time = time.time()
        read_attempts = 0
        status = None
        try:
            while not self.stop_reading and (time.time() - start_time) < 5:  # 5s timeout, adjust as needed
                read_attempts += 1
                uid = self.pn532.read_passive_target(timeout=0.5)
                if uid is not None:
                    # Convert UID bytes to single integer (big-endian)
                    uid_number = 0
                    for b in uid:
                        uid_number = (uid_number << 8) | b
                    logger.info(f"✅ PN532 read successful after {read_attempts} attempts: {uid} (int: {uid_number})")
                    self._stop_reading_internal()
                    if self.on_new_uid:
                        self.on_new_uid(uid_number)
                    status = {"status": "success", "uid": uid_number}
                    break
                time.sleep(0.2)
            if status is None:
                elapsed = time.time() - start_time
                logger.warning(f"❌ PN532 read timeout after {elapsed:.1f}s ({read_attempts} attempts)")
                status = {"status": "timeout", "error_message": "Card read timeout. Please try again."}
            self._stop_reading_internal()
        except Exception as e:
            logger.error(f"PN532 reading thread error: {e}")
            status = {"status": "error", "error_message": f"Reading error: {str(e)}"}
            self._stop_reading_internal()
        if self._result_callback:
            try:
                self._result_callback(status)
            except Exception as cb_e:
                logger.error(f"PN532 result callback error: {cb_e}")
        self._result_callback = None

    def _stop_reading_internal(self):
        self.stop_reading = True
        self.reading_active = False
        logger.info("🛑 PN532 reading stopped")

    def stop_reading_external(self):
        if self.reading_active:
            logger.info("Manually stopping PN532 reading...")
            self._stop_reading_internal()
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=1)

    def is_reading(self):
        return self.reading_active

    def stop(self):
        logger.info("Stopping PN532 reader...")
        self.stop_reading_external()
        self.initialized = False
        logger.info("PN532 reader stopped")

    def cleanup(self):
        self.stop()
