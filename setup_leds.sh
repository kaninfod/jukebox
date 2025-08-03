#!/bin/bash

echo "Installing LED strip dependencies..."
echo "===================================="

# Check if virtual environment exists
VENV_PATH="/home/pi/shared/jukebox/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please create the virtual environment first"
    exit 1
fi

echo "✅ Found virtual environment at $VENV_PATH"

# Update system
echo "1. Updating system packages..."
sudo apt-get update

# Install build dependencies
echo "2. Installing build tools..."
sudo apt-get install -y build-essential python3-dev scons swig

# Install Python library into virtual environment
echo "3. Installing rpi_ws281x Python library into virtual environment..."
source "$VENV_PATH/bin/activate"
pip install rpi_ws281x

# Check installation
echo "4. Testing installation..."
source "$VENV_PATH/bin/activate"
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
echo "Test with virtual environment:"
echo "  source $VENV_PATH/bin/activate"
echo "  sudo -E python3 minimal_led_test.py"
echo "  sudo -E python3 test_leds.py"
echo ""
echo "Note: LED control requires root privileges!"
echo "Use 'sudo -E' to preserve the virtual environment when running as root."
