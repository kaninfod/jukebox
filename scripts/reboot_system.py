#!/usr/bin/env python3
"""
Simple standalone reboot script for testing.
This script should be run outside of any systemd service context.
"""
import subprocess
import sys
import time

def main():
    print("=== Standalone Reboot Script ===")
    print(f"Running as: {subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()}")
    
    # Test different reboot approaches
    approaches = [
        {
            "name": "sudo systemctl reboot",
            "command": ["sudo", "/usr/bin/systemctl", "reboot"]
        },
        {
            "name": "direct /sbin/reboot",
            "command": ["/sbin/reboot"]
        },
        {
            "name": "systemctl reboot (no sudo)",
            "command": ["/usr/bin/systemctl", "reboot"]
        },
        {
            "name": "shutdown -r now",
            "command": ["/sbin/shutdown", "-r", "now"]
        },
        {
            "name": "sudo reboot",
            "command": ["sudo", "reboot"]
        }
    ]
    
    for approach in approaches:
        print(f"\n--- Testing: {approach['name']} ---")
        try:
            result = subprocess.run(
                approach['command'],
                capture_output=True,
                text=True,
                timeout=10
            )
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            
            if result.returncode == 0:
                print(f"✅ {approach['name']} succeeded! System should reboot...")
                break
            else:
                print(f"❌ {approach['name']} failed")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {approach['name']} timed out (system might be rebooting)")
            break
        except Exception as e:
            print(f"💥 {approach['name']} exception: {e}")
    
    print("\nIf you see this message, none of the reboot commands worked.")

if __name__ == "__main__":
    main()