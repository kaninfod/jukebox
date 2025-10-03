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
        # Metric: count PN532Reader object creations
        try:
            from app.metrics.collector import metrics
            metrics.inc("pn532reader_created")
        except Exception as e:
            logger.debug(f"Metric increment failed: {e}")

    def _init_pn532(self):
        """
        Initialize and return a PN532 instance (I2C).
        Returns: pn532 object
        Throws: Exception if initialization fails
        """
        import busio, board
        from adafruit_pn532.i2c import PN532_I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        pn532 = PN532_I2C(i2c, debug=True)
        pn532.SAM_configuration()
        logger.info("PN532 initialized and SAM configured.")
        return pn532        

    def _poll_for_card(self, pn532, timeout=10):
        """Poll for a card and return UID or None."""
        start_time = time.time()
        uid = None
        while (time.time() - start_time) < timeout:
            uid = pn532.read_passive_target(timeout=0.5)
            if uid is not None:
                logger.info(f"Found card with UID: {[hex(i) for i in uid]}")
                return uid
            time.sleep(0.1)
        logger.warning("Timeout waiting for card.")
        return None

    def _read_block(self, pn532, uid, block_number, key=b'\xFF\xFF\xFF\xFF\xFF\xFF', mifare_cmd=0x60):
        """Authenticate and read a block, return bytes or None."""
        auth = pn532.mifare_classic_authenticate_block(uid, block_number, mifare_cmd, key)
        logger.info(f"Authenticating for read block {block_number}: {auth}")
        if not auth:
            return None
        return pn532.mifare_classic_read_block(block_number)
    
    @staticmethod
    def encode_string_for_block(s):
        """Encode a string to 16 bytes for Mifare Classic block (pad/truncate as needed)."""
        return s.encode("utf-8")[:16].ljust(16, b' ')

    @staticmethod
    def decode_block_to_string(block_bytes):
        """Decode a 16-byte block to a string, stripping padding."""
        if not block_bytes:
            return None
        return block_bytes.decode("utf-8", errors="replace").rstrip(' ')

    def write_data(self, data_dict, timeout=10, result_callback=None):
        """
        Write a dict of {name: value} to the configured RFID blocks.
        - data_dict: dict with keys matching config.RFID_BLOCKS (e.g., {"album_id": "123", "name": "Test"})
        - timeout: seconds to wait for card
        Returns: dict with status, uid, and message
        """
        from app.config import Config
        MIFARE_CMD_AUTH_A = 0x60
        KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'
        try:
            pn532 = self._init_pn532()
            logger.info(f"Waiting for card to write to blocks {Config.RFID_BLOCKS}...")
            uid = self._poll_for_card(pn532, timeout=timeout)
            if uid is None:
                return {"status": "timeout", "message": "Timeout waiting for card."}
            else:
                uid_number = 0
                for b in uid:
                    uid_number = (uid_number << 8) | b
                # Write each configured block
                block_data = {}
                for name, block_number in Config.RFID_BLOCKS.items():
                    value = data_dict.get(name, "")
                    data = self.encode_string_for_block(value)
                    auth = pn532.mifare_classic_authenticate_block(uid, block_number, MIFARE_CMD_AUTH_A, KEY)
                    logger.info(f"Authenticating for write to {name} (block {block_number}): {auth}")
                    if not auth:
                        return {"status": "auth_failed", "message": f"Authentication failed for {name}!", "uid": uid}
                    write_ok = pn532.mifare_classic_write_block(block_number, data)
                    if not write_ok:
                        logger.error(f"Write failed for {name} (block {block_number})!")
                        block_data[name] = None
                    else:
                        block_data[name] = value
                        logger.debug(f"Wrote block {block_number} ({name}): {value}")
                _status = {"status": "success", "uid": uid_number, "blocks": block_data}
        except Exception as e:
            logger.error(f"PN532 write error: {e}")
            _status = {"status": "error", "error_message": f"Write error: {str(e)}"}
        if result_callback:
            try:
                result_callback(_status)
            except Exception as cb_e:
                logger.error(f"PN532 write result callback error: {cb_e}")


    def start_reading(self, result_callback=None):
        """
        Instantiates and initializes the PN532, performs a single read, then reads only configured blocks, then cleans up.
        Returns UID and named block data in a dict.
        """
        from app.config import Config
        status = None
        try:
            pn532 = self._init_pn532()
            logger.info("PN532 RFID reader initialized successfully (one-shot)")
            uid = self._poll_for_card(pn532, timeout=5)
            if uid is None:
                status = {"status": "timeout", "error_message": "Card read timeout. Please try again."}
            else:
                uid_number = 0
                for b in uid:
                    uid_number = (uid_number << 8) | b
                # if self.on_new_uid:
                #     self.on_new_uid(uid_number)
                MIFARE_CMD_AUTH_A = 0x60
                key = b'\xFF\xFF\xFF\xFF\xFF\xFF'
                block_data = {}
                for name, block in Config.RFID_BLOCKS.items():
                    try:
                        data = self._read_block(pn532, uid, block, key, MIFARE_CMD_AUTH_A)
                        block_data[name] = self.decode_block_to_string(data)
                        logger.debug(f"Block {block} ({name}): {block_data[name]}")
                    except Exception as e:
                        logger.debug(f"Block {block} ({name}): Exception {e}")
                        block_data[name] = None
                status = {"status": "success", "uid": uid_number, "blocks": block_data}
        except Exception as e:
            logger.error(f"PN532 one-shot read error: {e}")
            status = {"status": "error", "error_message": f"Reading error: {str(e)}"}
        if result_callback:
            try:
                result_callback(status)
            except Exception as cb_e:
                logger.error(f"PN532 result callback error: {cb_e}")
        # No persistent state to clean up