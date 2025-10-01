import threading
import time
import logging
from digitalio import DigitalInOut
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

logger = logging.getLogger(__name__)


# One-shot PN532 reader: instantiate, read, and cleanup per use
class PN532Reader:
    def __init__(self, on_new_uid=None):
        self.on_new_uid = on_new_uid

    def start_reading(self, result_callback=None):
        """
        Instantiates and initializes the PN532, performs a single read, then cleans up.
        Runs synchronously in the calling thread.
        """
        import busio, board
        from adafruit_pn532.i2c import PN532_I2C
        status = None
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            pn532 = PN532_I2C(i2c, debug=False)
            pn532.SAM_configuration()
            logger.info("PN532 RFID reader initialized successfully (one-shot)")
            start_time = time.time()
            read_attempts = 0
            while (time.time() - start_time) < 5:
                read_attempts += 1
                uid = pn532.read_passive_target(timeout=0.5)
                if uid is not None:
                    uid_number = 0
                    for b in uid:
                        uid_number = (uid_number << 8) | b
                    logger.info(f"✅ PN532 read successful after {read_attempts} attempts: {uid} (int: {uid_number})")
                    if self.on_new_uid:
                        self.on_new_uid(uid_number)
                    status = {"status": "success", "uid": uid_number}
                    break
                time.sleep(0.2)
            if status is None:
                elapsed = time.time() - start_time
                logger.warning(f"❌ PN532 read timeout after {elapsed:.1f}s ({read_attempts} attempts)")
                status = {"status": "timeout", "error_message": "Card read timeout. Please try again."}
        except Exception as e:
            logger.error(f"PN532 one-shot read error: {e}")
            status = {"status": "error", "error_message": f"Reading error: {str(e)}"}
        if result_callback:
            try:
                result_callback(status)
            except Exception as cb_e:
                logger.error(f"PN532 result callback error: {cb_e}")
        # No persistent state to clean up