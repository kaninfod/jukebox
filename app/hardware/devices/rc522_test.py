

from pirc522 import RFID
import lgpio
import logging

logger = logging.getLogger("rc522_test")
logging.basicConfig(level=logging.DEBUG)

CS_PIN = 7  # Change if your wiring uses a different pin

def reset_all_gpio():
    # BCM GPIO pins 2-27 (common on Pi models)
    h = lgpio.gpiochip_open(0)
    pins = list(range(2, 28))
    for pin in pins:
        try:
            lgpio.gpio_claim_input(h, pin)
        except Exception as e:
            logger.debug(f"Failed to reset pin {pin}: {e}")
    logger.info("All GPIO pins set to input mode (lgpio).")
    lgpio.gpiochip_close(h)

try:
    reset_all_gpio()
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(h, CS_PIN)
    logger.info(f"GPIO setup complete for CS_PIN={CS_PIN} (lgpio)")
    rdr = RFID(bus=0, device=1, pin_mode=None)  # pin_mode not needed for lgpio
    logger.info("RC522 RFID reader initialized successfully!")
    # Try a simple read to verify communication
    uid = rdr.read_id(True)
    logger.info(f"RC522 read_id returned: {uid}")
    rdr.cleanup()
    logger.info("RC522 cleanup complete.")
    lgpio.gpiochip_close(h)
except Exception as e:
    logger.error(f"RC522 init or read failed: {e}")
    logger.error("Check wiring, pin numbers, and library compatibility.")
