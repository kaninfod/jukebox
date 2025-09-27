import time
import board
import busio
from digitalio import DigitalInOut
import digitalio
from adafruit_pn532.spi import PN532_SPI

# Mifare Classic Key A command (not always exported by library)
MIFARE_CMD_AUTH_A = 0x60


# SPI and CS setup
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = DigitalInOut(board.D7)
pn532 = PN532_SPI(spi, cs_pin, debug=False)
pn532.SAM_configuration()



album_id = input("Enter album_id to write to the card (e.g., al-288): ").strip()
data = f"album_id:{album_id}".encode("utf-8")[:16].ljust(16, b' ')


print("\nNow place the card on the reader to write...")
while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is not None:
        print("Found card with UID:", [hex(i) for i in uid])
        break
    time.sleep(0.1)


block_number = 4  # First writable block
key = b'\xFF\xFF\xFF\xFF\xFF\xFF'  # Default key

auth_write = pn532.mifare_classic_authenticate_block(uid, block_number, MIFARE_CMD_AUTH_A, key)
print(f"Authenticating for write: {auth_write}")
if auth_write:
    if pn532.mifare_classic_write_block(block_number, data):
        print("Write successful!")
    else:
        print("Write failed!")
else:
    print("Authentication failed!")


input("\nRemove and re-place the card to read UID and value. Press Enter when ready...")
print("Waiting for card...")
while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is not None:
        print("Found card with UID:", [hex(i) for i in uid])
        # Convert UID to integer
        uid_number = 0
        for b in uid:
            uid_number = (uid_number << 8) | b
        print("UID as integer:", uid_number)
        # Authenticate and read block
        auth_read = pn532.mifare_classic_authenticate_block(uid, block_number, MIFARE_CMD_AUTH_A, key)
        print(f"Authenticating for read: {auth_read}")
        if auth_read:
            read_data = pn532.mifare_classic_read_block(block_number)
            if read_data:
                print("Read value:", read_data.decode("utf-8", errors="replace").strip())
            else:
                print("Read failed!")
        else:
            print("Authentication failed!")
        break
    time.sleep(0.1)
