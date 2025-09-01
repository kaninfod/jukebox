from luma.core.interface.serial import  spi
from luma.core.render import canvas
from luma.lcd.device import ili9488
import RPi.GPIO as GPIO





spi = spi(port=0, device=0, gpio_CS=8, gpio_DC=23, gpio_RST=24, bus_speed_hz=32000000)
device = ili9488(spi)

GPIO.setup(20, GPIO.OUT)
GPIO.output(20, GPIO.LOW)



# # Send test data
# try:
#     response = spi.xfer2([0xAA])
#     print("SPI response:", response)
# except Exception as e:
#     print("SPI communication failed:", e)
# finally:
#     spi.close()





device.backlight(True)
print("Display backlight turned on")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((30, 40), "Hello World", fill="red")

import spidev

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0
spi.max_speed_hz = 50000

# Send test data
try:
    response = spi.xfer2([0xAA])
    print("SPI response:", response)
except Exception as e:
    print("SPI communication failed:", e)
finally:
    spi.close()
