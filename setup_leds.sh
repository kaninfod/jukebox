#!/bin/bash

echo "Installing LED strip dependencies..."
echo "===================================="

# Update system
echo "1. Updating system packages..."
sudo apt-get update

# Install build dependencies
echo "2. Installing build tools..."
sudo apt-get install -y build-essential python3-dev scons swig

# Install Python library
echo "3. Installing rpi_ws281x Python library..."
pip install rpi_ws281x

# Check installation
echo "4. Testing installation..."
python3 -c "
try:
    from rpi_ws281x import PixelStrip, Color
    print('✓ rpi_ws281x installed successfully')
except ImportError as e:
    print(f'✗ Installation failed: {e}')
    exit(1)
"

echo ""
echo "Installation complete!"
echo ""
echo "Hardware connections:"
echo "  LED Data Pin → GPIO 13 (Physical pin 33)"
echo "  LED VCC      → 5V power supply"
echo "  LED GND      → Common ground"
echo ""
echo "Test with:"
echo "  sudo python3 minimal_led_test.py"
echo "  sudo python3 test_leds.py"
echo ""
echo "Note: LED control requires root privileges!"
