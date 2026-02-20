#!/usr/bin/env python3
"""
Test script for Raspberry Pi display brightness control.
Auto-detects backlight device and tests read/write permissions.
Run as the jukebox user to identify permission issues.
"""

import os
import sys
import glob
import subprocess
from pathlib import Path

class BrightnessTest:
    def __init__(self):
        self.backlight_path = None
        self.brightness_file = None
        self.max_brightness_file = None
        self.max_brightness = None
        self.current_brightness = None
    
    def find_backlight_device(self):
        """Auto-discover backlight device path."""
        print("=" * 60)
        print("STEP 1: Finding backlight device...")
        print("=" * 60)
        
        backlight_dir = "/sys/class/backlight"
        
        if not os.path.exists(backlight_dir):
            print(f"❌ Backlight directory not found: {backlight_dir}")
            return False
        
        devices = os.listdir(backlight_dir)
        if not devices:
            print(f"❌ No backlight devices found in {backlight_dir}")
            return False
        
        # Use the first device (or you can specify a specific one)
        device = devices[0]
        self.backlight_path = os.path.join(backlight_dir, device)
        self.brightness_file = os.path.join(self.backlight_path, "brightness")
        self.max_brightness_file = os.path.join(self.backlight_path, "max_brightness")
        
        print(f"✅ Found backlight device: {device}")
        print(f"   Path: {self.backlight_path}")
        return True
    
    def check_permissions(self):
        """Check file permissions and ownership."""
        print("\n" + "=" * 60)
        print("STEP 2: Checking file permissions...")
        print("=" * 60)
        
        current_user = os.getenv("USER", "unknown")
        current_uid = os.getuid()
        print(f"Current user: {current_user} (UID: {current_uid})")
        
        for fpath in [self.brightness_file, self.max_brightness_file]:
            if os.path.exists(fpath):
                stat_info = os.stat(fpath)
                mode = oct(stat_info.st_mode)[-3:]
                owner_uid = stat_info.st_uid
                
                # Get owner name
                try:
                    import pwd
                    owner_name = pwd.getpwuid(owner_uid).pw_name
                except:
                    owner_name = f"UID:{owner_uid}"
                
                can_read = os.access(fpath, os.R_OK)
                can_write = os.access(fpath, os.W_OK)
                
                print(f"\n{fpath}")
                print(f"  Owner: {owner_name} (UID: {owner_uid})")
                print(f"  Permissions: {mode}")
                print(f"  Read: {'✅ Yes' if can_read else '❌ No'}")
                print(f"  Write: {'✅ Yes' if can_write else '❌ No'}")
            else:
                print(f"\n❌ File not found: {fpath}")
                return False
        
        return True
    
    def read_max_brightness(self):
        """Read max brightness value."""
        print("\n" + "=" * 60)
        print("STEP 3: Reading max brightness...")
        print("=" * 60)
        
        try:
            with open(self.max_brightness_file, 'r') as f:
                self.max_brightness = int(f.read().strip())
            print(f"✅ Max brightness: {self.max_brightness}")
            return True
        except PermissionError:
            print(f"❌ Permission denied reading {self.max_brightness_file}")
            print("   Try: sudo chmod 644 /sys/class/backlight/*/max_brightness")
            return False
        except Exception as e:
            print(f"❌ Error reading max brightness: {e}")
            return False
    
    def read_current_brightness(self):
        """Read current brightness value."""
        print("\n" + "=" * 60)
        print("STEP 4: Reading current brightness...")
        print("=" * 60)
        
        try:
            with open(self.brightness_file, 'r') as f:
                self.current_brightness = int(f.read().strip())
            brightness_percent = (self.current_brightness / self.max_brightness * 100) if self.max_brightness else 0
            print(f"✅ Current brightness: {self.current_brightness} ({brightness_percent:.1f}%)")
            return True
        except PermissionError:
            print(f"❌ Permission denied reading {self.brightness_file}")
            print("   Try: sudo chmod 644 /sys/class/backlight/*/brightness")
            return False
        except Exception as e:
            print(f"❌ Error reading current brightness: {e}")
            return False
    
    def test_write_brightness(self):
        """Test writing a new brightness value."""
        print("\n" + "=" * 60)
        print("STEP 5: Testing brightness write...")
        print("=" * 60)
        
        # Calculate 50% brightness
        test_brightness = int(self.max_brightness * 0.5)
        
        print(f"Attempting to set brightness to: {test_brightness} (50%)")
        
        try:
            with open(self.brightness_file, 'w') as f:
                f.write(str(test_brightness))
            print(f"✅ Successfully wrote brightness value")
            
            # Read it back to verify
            with open(self.brightness_file, 'r') as f:
                new_brightness = int(f.read().strip())
            
            if new_brightness == test_brightness:
                print(f"✅ Verification successful: brightness is now {new_brightness}")
                return True
            else:
                print(f"⚠️  Unexpected value read back: {new_brightness} (expected {test_brightness})")
                return False
        except PermissionError:
            print(f"❌ Permission denied writing to {self.brightness_file}")
            print("   You need write permission to the brightness file.")
            print("\n   Fix options:")
            print("   1. Add udev rule (recommended)")
            print("   2. Add sudoers rule (if using sudo)")
            print("   3. Change file permissions (temporary until reboot)")
            return False
        except Exception as e:
            print(f"❌ Error writing brightness: {e}")
            return False
    
    def restore_brightness(self):
        """Restore original brightness value."""
        print("\n" + "=" * 60)
        print("STEP 6: Restoring original brightness...")
        print("=" * 60)
        
        try:
            with open(self.brightness_file, 'w') as f:
                f.write(str(self.current_brightness))
            print(f"✅ Restored brightness to: {self.current_brightness}")
            return True
        except Exception as e:
            print(f"❌ Error restoring brightness: {e}")
            return False
    
    def print_permission_solutions(self):
        """Print suggested permission fixes."""
        print("\n" + "=" * 60)
        print("PERMISSION SOLUTIONS")
        print("=" * 60)
        
        print("\n📋 OPTION 1: udev rule (Recommended - permanent solution)")
        print("-" * 60)
        print("Create /etc/udev/rules.d/99-backlight.rules:")
        print("  SUBSYSTEM==\"backlight\", ACTION==\"add\", RUN+=\"/bin/chmod 666 /sys%p/brightness\"")
        print("\nThen reload udev:")
        print("  sudo udevadm control --reload")
        print("  sudo udevadm trigger")
        
        print("\n📋 OPTION 2: sudoers rule (if using sudo)")
        print("-" * 60)
        print("Run: sudo visudo")
        print("Add this line:")
        print("  jukebox ALL=(ALL) NOPASSWD: /bin/tee /sys/class/backlight/*/brightness")
        
        print("\n📋 OPTION 3: Quick test (temporary)")
        print("-" * 60)
        print("  sudo chmod 666 /sys/class/backlight/*/brightness")
        print("  sudo chmod 644 /sys/class/backlight/*/max_brightness")
        print("⚠️  Note: This resets after reboot")
    
    def run(self):
        """Run all tests."""
        print("\n🔆 RASPBERRY PI BRIGHTNESS CONTROL TEST 🔆\n")
        
        if not self.find_backlight_device():
            return False
        
        if not self.check_permissions():
            return False
        
        if not self.read_max_brightness():
            self.print_permission_solutions()
            return False
        
        if not self.read_current_brightness():
            self.print_permission_solutions()
            return False
        
        if not self.test_write_brightness():
            self.print_permission_solutions()
            return False
        
        if not self.restore_brightness():
            return False
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🎉 Brightness control is working correctly!")
        print("You can now integrate this into the app.\n")
        return True

if __name__ == "__main__":
    tester = BrightnessTest()
    success = tester.run()
    sys.exit(0 if success else 1)
