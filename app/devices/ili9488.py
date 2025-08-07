from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from PIL import Image, ImageDraw, ImageFont
from luma.core.render import canvas
from app.config import config
import RPi.GPIO as GPIO

class ILI9488:
    def __init__(self):
        # Initialize display with backlight control
        # Note: The backlight turns OFF during device initialization and the 
        # device.backlight() method doesn't seem to work with our hardware setup
        self.serial = spi(port=0, device=0, gpio_CS=8, gpio_DC=23, gpio_RST=24, bus_speed_hz=32000000)
        self.device = ili9488(self.serial, rotate=0, gpio_LIGHT=config.DISPLAY_BACKLIGHT_GPIO, active_low=False)
        
        # Try to turn backlight on, but this may not work with our hardware
        try:
            self.device.backlight(True)
        except Exception as e:
            print(f"Backlight control may not work: {e}")
        
        try:
            self.font = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 30)
        except (OSError, ImportError) as e:
            print(f"Font loading failed: {e}, using default font")
            self.font = ImageFont.load_default()


    def cleanup(self):
        """Clean up GPIO resources (normal cleanup for app restart)"""
        try:
            self.device.backlight(False)
            print("Display: Backlight turned off")
        except Exception as e:
            print(f"Display: Failed to turn off backlight: {e}")
        print("Display cleanup: luma will handle all GPIO cleanup")

    def turn_off_backlight(self):
        """Turn off the display backlight"""
        try:
            self.device.backlight(False)
            print("Display: Backlight turned off")
        except Exception as e:
            print(f"Display: Failed to turn off backlight: {e}")

    def turn_on_backlight(self):
        """Turn on the display backlight"""
        try:
            self.device.backlight(True)
            print("Display: Backlight turned on")
        except Exception as e:
            print(f"Display: Failed to turn on backlight: {e}")

    def power_off(self):
        """Turn off the display using hardware power switching via S8550 transistor"""
        try:
            print("Display: Attempting hardware power OFF...")
            # Set GPIO as input (floating) to turn OFF display
            # S8550 transistor: floating input = 3.6V (OFF), output LOW = 4.8V (ON)
            GPIO.setup(config.DISPLAY_POWER_GPIO, GPIO.IN)
            # Voltage measured: 3.6V (display OFF)
            print("Display: Hardware power OFF (S8550 transistor)")
            
        except Exception as e:
            print(f"Display: Hardware power OFF failed: {e}")
    
    def power_on(self):
        """Turn on the display using hardware power switching via S8550 transistor"""
        try:
            print("Display: Attempting hardware power ON...")
            # Set GPIO as output LOW to turn ON display
            # S8550 transistor: floating input = 3.6V (OFF), output LOW = 4.8V (ON)  
            GPIO.setup(config.DISPLAY_POWER_GPIO, GPIO.OUT)
            GPIO.output(config.DISPLAY_POWER_GPIO, GPIO.LOW)
            # Voltage measured: 4.8V (display ON)
            print("Display: Hardware power ON (S8550 transistor)")
            
        except Exception as e:
            print(f"Display: Hardware power ON failed: {e}")

    def display_image(self, text: str):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="green", fill="white")
            draw.text((30, 40), text, font=self.font, fill="green")
