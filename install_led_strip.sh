#!/bin/bash

# Install WS2811/WS2812 LED strip library for Raspberry Pi
# This script installs rpi_ws281x library into the virtual environment

echo "Installing rpi_ws281x library for LED strip control..."

# Check if virtual environment exists
VENV_PATH="/home/pi/shared/jukebox/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please create the virtual environment first or run from the correct location"
    exit 1
fi

echo "✅ Found virtual environment at $VENV_PATH"

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update

# Install dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y build-essential python3-dev scons swig

# Activate virtual environment and install the Python library
echo "🐍 Installing rpi_ws281x into virtual environment..."
source "$VENV_PATH/bin/activate"
pip install rpi_ws281x

echo "Installation complete!"
echo ""
echo "Hardware setup notes:"
echo "- LED strip data line should be connected to GPIO 13 (PWM1)"
echo "- LED strip power should be connected to appropriate 5V power supply"
echo "- LED strip ground should be connected to Raspberry Pi ground"
echo "- Consider adding a 330Ω resistor between GPIO 13 and LED data line"
echo "- Ensure adequate power supply for 6 LEDs (typically 5V 1A is sufficient)"
echo ""
echo "The LED strip will start with a warm glow effect and:"
echo "- Sync with music playback status (play/pause/standby)"
echo "- Adjust brightness based on volume level"
echo "- Provide ambient lighting during jukebox operation"
