
from pirc522 import RFID
import RPi.GPIO as GPIO
import threading
import time
from app.config import config
import logging

logger = logging.getLogger(__name__)

class RC522Reader:
    def __init__(self, cs_pin=7, on_new_uid=None, switch_pin=None, screen_manager=None):
        """
        Initialize RC522 RFID reader with switch-triggered reading.
        
        Args:
            cs_pin: Chip select pin for RC522 (default: 7)
            on_new_uid: Callback function called when new UID is detected
            switch_pin: GPIO pin for the card insertion switch (None for button-triggered mode)
            screen_manager: ScreenManager instance for showing loading feedback
        """
        logger.info("Initializing RC522 RFID Reader with switch-triggered reading...")
        
        self.cs_pin = cs_pin
        self.on_new_uid = on_new_uid
        self.switch_pin = switch_pin
        self.screen_manager = screen_manager
        self.rdr = None
        self.initialized = False
        self.reading_active = False
        self.read_thread = None
        self.stop_reading = False
        
        # Only disable warnings, don't cleanup all GPIO
        GPIO.setwarnings(False)
        
        try:
            self.rdr = RFID(bus=0, device=1, pin_mode=GPIO.BCM)
            self.initialized = True
            logger.info("RFID reader initialized successfully")
            
            # Set up switch pin if provided
            if self.switch_pin:
                GPIO.setup(self.switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                #TODO bouncetime should come from config
                GPIO.add_event_detect(self.switch_pin, GPIO.FALLING, callback=self._on_switch_activated, bouncetime=200)
                logger.info(f"RFID switch monitoring started on GPIO {self.switch_pin}")
                
        except Exception as e:
            logger.error(f"Failed to initialize RFID reader: {e}")
            logger.warning("Attempting to continue without RFID functionality...")
            self.initialized = False
    
    def _on_switch_activated(self, channel):
        """Handle switch activation (card inserted)"""
        if not self.initialized or self.reading_active:
            return
        
        logger.info("🃏 Card insertion detected - starting RFID read...")
        
        # Show RFID reading screen if screen manager is available
        if self.screen_manager:
            self.screen_manager.show_rfid_reading()
        
        self.start_reading()
    
    def start_reading(self):
        """Start RFID reading process with timeout"""
        if not self.initialized:
            logger.error("RFID reader not initialized, cannot start reading")
            return False
            
        if self.reading_active:
            logger.warning("RFID reading already in progress")
            return False
        
        logger.info(f"Starting RFID read with {config.RFID_READ_TIMEOUT}s timeout...")
        self.reading_active = True
        self.stop_reading = False
        
        # Start reading in separate thread
        self.read_thread = threading.Thread(target=self._read_with_timeout, daemon=True)
        self.read_thread.start()
        
        return True
    
    def _read_with_timeout(self):
        """Read RFID with timeout in separate thread"""
        start_time = time.time()
        read_attempts = 0
        
        try:
            while not self.stop_reading and (time.time() - start_time) < config.RFID_READ_TIMEOUT:
                try:
                    read_attempts += 1
                    
                    # Check for RFID tag
                    uid = self.rdr.read_id(True)
                    
                    if uid is not None:
                        # Successfully read tag
                        logger.info(f"✅ RFID read successful after {read_attempts} attempts: {uid}")
                        
                        # Stop reading and call callback
                        self._stop_reading_internal()
                        
                        if self.on_new_uid:
                            self.on_new_uid(uid)
                        return
                    
                    # Small delay between attempts
                    time.sleep(0.2)
                    
                except Exception as e:
                    # Suppress common RFID communication errors (E1, E2, etc.)
                    if "E1" not in str(e) and "E2" not in str(e):
                        print(f"RFID read error: {e}")
                    time.sleep(0.1)
            
            # Timeout reached without successful read
            elapsed = time.time() - start_time
            print(f"❌ RFID read timeout after {elapsed:.1f}s ({read_attempts} attempts)")
            
            # Show error screen if screen manager is available
            if self.screen_manager:
                self.screen_manager.show_rfid_screen({
                    "status": "error",
                    "error_message": "Card read timeout. Please try again."
                })
        
            self._stop_reading_internal()
            
        except Exception as e:
            print(f"RFID reading thread error: {e}")
            
            # Show error screen if screen manager is available
            if self.screen_manager:
                self.screen_manager.show_rfid_screen({
                    "status": "error",
                    "error_message": f"Reading error: {str(e)}"
                })
            
            self._stop_reading_internal()
    
    def _stop_reading_internal(self):
        """Internal method to stop reading"""
        self.stop_reading = True
        self.reading_active = False
        print("🛑 RFID reading stopped")
    
    def stop_reading_external(self):
        """External method to stop reading (can be called from outside)"""
        if self.reading_active:
            print("Manually stopping RFID reading...")
            self._stop_reading_internal()
            
            # Wait for thread to finish
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=1)
    
    def is_reading(self):
        """Check if RFID reading is currently active"""
        return self.reading_active
    
    def stop(self):
        """Stop the RFID reader and cleanup"""
        print("Stopping RFID reader...")
        
        # Stop any active reading
        self.stop_reading_external()
        
        # Cleanup switch pin if configured
        if self.switch_pin:
            try:
                GPIO.remove_event_detect(self.switch_pin)
                print(f"RFID switch event detection removed from GPIO {self.switch_pin}")
            except Exception as e:
                print(f"Error removing switch event detection: {e}")
        
        # Cleanup RFID reader
        if self.rdr:
            try:
                self.rdr.cleanup()
                print("RFID reader cleaned up")
            except Exception as e:
                print(f"Error cleaning up RFID reader: {e}")
        
        self.initialized = False
        print("RFID reader stopped")
    
    def cleanup(self):
        """Alias for stop() for consistency with other devices"""
        self.stop()