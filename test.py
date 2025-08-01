from pirc522 import RFID
import RPi.GPIO as GPIO
import time

IRQ_PIN = 19  # BCM numbering

def irq_callback(channel):
    uid = rdr.read_id(True)
    print(f"IRQ Callback: UID={uid}")

if __name__ == "__main__":
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()  # Clean up any previous state

    print("Initializing RC522 RFID Reader with IRQ...")
    rdr = RFID(bus=0, device=1, pin_mode=GPIO.BCM, pin_irq=None)

    # Configure RC522 to enable RX interrupt and allow IRQ pin to go low
    CommIEnReg = 0x02  # Enable register
    CommIrqReg = 0x04  # IRQ flag register
    rdr.dev_write(CommIEnReg, 0x20 | 0x80)  # Enable interrupt on Rx (bit 5) and set bit 7 to activate IRQ pin
    rdr.dev_write(CommIrqReg, 0x7F)         # Clear any previous interrupt flags

    GPIO.setup(IRQ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(IRQ_PIN, GPIO.FALLING, callback=irq_callback, bouncetime=200)

    print("Waiting for RFID tags... (Press Ctrl+C to exit)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.remove_event_detect(IRQ_PIN)
        rdr.dev_write(CommIrqReg, 0x7F)  # Clear any IRQ flags
        rdr.cleanup()
        GPIO.cleanup()