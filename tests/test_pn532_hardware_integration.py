"""
Test script to initialize the HardwareManager and trigger a PN532 RFID read without physical switch/button.
"""
import time
from app.hardware.hardware import HardwareManager
from app.config import config
from app.core import event_bus

# Optionally, set a DEV_MODE flag in your config for test environments
setattr(config, "DEV_MODE", True)

# Dummy event bus if needed (replace with your actual event bus if required)
# from app.core import EventBus
# event_bus = EventBus()

# Initialize HardwareManager
hardware_manager = HardwareManager(config, event_bus)
hardware_manager.initialize_hardware()

# Directly trigger the RFID read (simulate switch/button)
hardware_manager._on_rfid_switch_activated(0)

# Wait for the read to complete (adjust as needed)
time.sleep(6)

print("Test complete.")
