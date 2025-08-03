from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from PIL import Image, ImageDraw, ImageFont
from luma.core.render import canvas

class ILI9488:
    def __init__(self):
        # Initialize display with backlight control on GPIO 18 (default)
        self.serial = spi(port=0, device=0, gpio_CS=8, gpio_DC=23, gpio_RST=24, bus_speed_hz=32000000)
        self.device = ili9488(self.serial, rotate=0, gpio_LIGHT=18, active_low=False)
        
        # Set backlight to maximum brightness and leave it on
        self.device.backlight(True)
        
        try:
            self.font = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 30)
        except (OSError, ImportError) as e:
            print(f"Font loading failed: {e}, using default font")
            self.font = ImageFont.load_default()


    def cleanup(self):
        """Clean up GPIO resources"""
        # No PWM to clean up anymore - luma handles all GPIO cleanup
        print("Display cleanup: luma will handle all GPIO cleanup")
        pass

    def display_image(self, text: str):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="green", fill="white")
            draw.text((30, 40), text, font=self.font, fill="green")
