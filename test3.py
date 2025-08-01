import RPi.GPIO as GPIO
import time

PIN = 19

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("Polling pin state (press Ctrl+C to exit)...")
    while True:
        state = GPIO.input(PIN)
        print("Pin state:", state)
        time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()