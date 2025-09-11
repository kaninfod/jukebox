#!/usr/bin/env python3
"""
KY-040 Rotary Encoder Test Script
Test and fine-tune the rotary encoder responsiveness and debouncing.
"""
import sys
import os
import time
import logging

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.hardware.devices.rotaryencoder import RotaryEncoder
from app.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class EncoderTester:
    def __init__(self):
        self.total_steps = 0
        self.cw_steps = 0
        self.ccw_steps = 0
        self.last_time = time.time()
        
    def encoder_callback(self, direction, position):
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        self.total_steps += 1
        if direction > 0:
            self.cw_steps += 1
            dir_str = "CW ➡️"
        else:
            self.ccw_steps += 1
            dir_str = "CCW ⬅️"
            
        print(f"{dir_str} | Position: {position:+4d} | Δt: {time_diff*1000:5.1f}ms | Total: {self.total_steps}")
        self.last_time = current_time
    
    def print_stats(self):
        print(f"\n📊 Encoder Statistics:")
        print(f"   Total steps: {self.total_steps}")
        print(f"   Clockwise: {self.cw_steps}")
        print(f"   Counter-clockwise: {self.ccw_steps}")
        if self.total_steps > 0:
            print(f"   CW ratio: {self.cw_steps/self.total_steps*100:.1f}%")

def main():
    print("🔄 KY-040 Rotary Encoder Test")
    print("=" * 40)
    print(f"Pin A: GPIO {config.ROTARY_ENCODER_PIN_A}")
    print(f"Pin B: GPIO {config.ROTARY_ENCODER_PIN_B}")
    print(f"Bouncetime: {config.ENCODER_BOUNCETIME}ms")
    print("\nTurn the encoder to test responsiveness...")
    print("Press Ctrl+C to exit and see statistics\n")
    
    tester = EncoderTester()
    
    try:
        encoder = RotaryEncoder(
            pin_a=config.ROTARY_ENCODER_PIN_A,
            pin_b=config.ROTARY_ENCODER_PIN_B,
            callback=tester.encoder_callback,
            bouncetime=config.ENCODER_BOUNCETIME
        )
        
        if not encoder.initialized:
            print("❌ Failed to initialize encoder!")
            return
            
        print("✅ Encoder initialized successfully!")
        print("🎯 Turn the encoder slowly and quickly to test debouncing...")
        
        # Keep the script running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test stopped by user")
        tester.print_stats()
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        
    finally:
        try:
            encoder.cleanup()
            print("🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    main()
