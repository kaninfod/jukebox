from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from PIL import Image, ImageDraw, ImageFont
from luma.core.render import canvas

class ILI9488:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_CS=8, gpio_DC=23, gpio_RST=24, gpio_LIGHT=18, bus_speed_hz=32000000)
        self.device = ili9488(self.serial, rotate=0, gpio_LIGHT=18, active_low=False)
        self.device.backlight(True)
        self.font = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 30)

    def display_image(self, text: str):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
            draw.text((30, 40), text, font=self.font, fill="white")
