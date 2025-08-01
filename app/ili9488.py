from luma.core.interface.serial import spi
from luma.lcd.device import ili9488
from PIL import Image, ImageDraw, ImageFont
from luma.core.render import canvas
import RPi.GPIO as GPIO
import time

class ILI9488:
    def __init__(self):
        # Initialize display with backlight control on GPIO 18 (default)
        self.serial = spi(port=0, device=0, gpio_CS=8, gpio_DC=23, gpio_RST=24, bus_speed_hz=32000000)
        self.device = ili9488(self.serial, rotate=0, gpio_LIGHT=18, active_low=False)
        
        # Use luma's built-in backlight control
        self.device.backlight(True)
        self.pwm = GPIO.PWM(18, 1000)
        self.pwm.start(0)
        self.fade_in()
        try:
            self.font = ImageFont.truetype("/home/pi/shared/jukebox/fonts/opensans/OpenSans-Regular.ttf", 30)
        except (OSError, ImportError) as e:
            print(f"Font loading failed: {e}, using default font")
            self.font = ImageFont.load_default()

    def set_brightness(self, brightness):
        """Set backlight brightness using luma's backlight control"""
        brightness = max(0, min(100, brightness))  # Clamp between 0-100
        # Convert to boolean for luma's backlight control
        # For now, we'll use simple on/off (luma doesn't have PWM control built-in)
        self.pwm.ChangeDutyCycle(brightness)


    def cleanup(self):
        """Clean up GPIO resources"""
        # No need to cleanup GPIO since luma handles it
        pass

    def fade_in(self):
        for duty_cycle in range(0, 101, 1):
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.01)

    def fade_out(self):
        for duty_cycle in range(100, -1, -1):
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.01)

    def display_image(self, text: str):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="green", fill="white")
            draw.text((30, 40), text, font=self.font, fill="green")

    def cleanup(self):
        """Clean up PWM and GPIO resources"""
        self.pwm.stop()
        GPIO.cleanup()
