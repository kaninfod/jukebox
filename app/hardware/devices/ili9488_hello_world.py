import time
import logging
from app.config import config
from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from luma.core.render import canvas
from luma.core.framebuffer import diff_to_previous
from PIL import ImageFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ili9488-test")

def main():
    # Setup SPI and display using config
    serial = spi(
        port=0,
        device=0,
        gpio_CS=config.DISPLAY_GPIO_CS,
        gpio_DC=config.DISPLAY_GPIO_DC,
        gpio_RST=config.DISPLAY_GPIO_RST,
        bus_speed_hz=48000000
    )
    device = ili9488(
        serial,
        rotate=config.DISPLAY_ROTATION,
        gpio_LIGHT=getattr(config, "DISPLAY_BACKLIGHT_GPIO", 18),
        active_low=False,
        framebuffer=diff_to_previous()
    )
    try:
        font = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
    logger.info("Drawing Hello World to display...")
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((30, 40), "Hello World!", font=font, fill="red")
    time.sleep(5)
    logger.info("Test complete. Turning off backlight.")
    try:
        device.backlight(False)
    except Exception:
        pass

if __name__ == "__main__":
    main()
