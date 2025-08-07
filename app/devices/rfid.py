from pirc522 import RFID
import RPi.GPIO as GPIO
import threading
import time
from app.config import config





class RC522Reader:
    def __init__(self, cs_pin=7, poll_interval=1.0, on_new_uid=None):  # Increased from 0.5 to 1.0 seconds
        print("Initializing RC522 RFID Reader with polling...")
        
        # Only disable warnings, don't cleanup all GPIO
        GPIO.setwarnings(False)
        
        try:
            self.rdr = RFID(bus=0, device=1, pin_mode=GPIO.BCM)
        except RuntimeError as e:
            print(f"Failed to initialize RFID reader: {e}")
            print("Attempting to continue without RFID functionality...")
            self.rdr = None
            return
        
        self.latest_uid = None
        self._on_new_uid = on_new_uid  # callback function
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self):
        if self.rdr is None:
            print("RFID reader not initialized, skipping polling...")
            return
            
        while not self._stop_event.is_set():
            try:
                uid = self.rdr.read_id(True)
                #print(f"Polled UID: {uid}")
                if uid is not None and uid != self.latest_uid:
                    #print(f"New tag detected via polling! UID: {uid}")
                    self.latest_uid = uid
                    if self._on_new_uid:
                        print(f"Calling on_new_uid with UID: {uid}")
                        self._on_new_uid(uid)
            except Exception as e:
                # Suppress common RFID communication errors (E1, E2, etc.)
                if "E1" not in str(e) and "E2" not in str(e):
                    print(f"RFID read error: {e}")
            #elif uid is None:
                #if self.latest_uid is not None:
                    #print("Tag removed.")
                #self.latest_uid = None
            time.sleep(self._poll_interval)


    def get_latest_uid(self):
        return self.latest_uid

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.rdr.cleanup()