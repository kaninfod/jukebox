import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print("19: ", GPIO.input(19))
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print("26: ", GPIO.input(26))
