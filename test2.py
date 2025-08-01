import RPi.GPIO as GPIO
import time

PIN = 19

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#GPIO.cleanup()
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def cb(channel):
    print("Edge detected!")

GPIO.add_event_detect(PIN, GPIO.FALLING, callback=cb, bouncetime=200)

print("Waiting for edge... (Ctrl+C to exit)")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.remove_event_detect(PIN)
    GPIO.cleanup()