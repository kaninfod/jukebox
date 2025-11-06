#!/bin/bash
# Script to perform system shutdown
# This script is called by cron when a shutdown trigger is detected

# Set PATH explicitly for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Logging function
log_message() {
    echo "$(date): do_shutdown.sh: $1" | tee -a /home/pi/shared/jukebox/tmp/shutdown.log
}

log_message "=========================================="
log_message "System shutdown script started"
log_message "=========================================="

# Log environment info
log_message "User: $(whoami)"
log_message "PWD: $PWD"
log_message "PATH: $PATH"

# Step 1: Try to gracefully shutdown mediaplayer first
log_message "Attempting to gracefully shutdown mediaplayer..."
# Note: We could emit an event or call the API here if needed
# For now, let's proceed directly to system shutdown

# Step 2: Execute system shutdown
log_message "Executing system shutdown command..."
log_message "Command: sudo /usr/bin/systemctl poweroff"

# Execute the shutdown command
sudo /usr/bin/systemctl poweroff

# Note: If we reach this point, the shutdown command failed
log_message "ERROR: Shutdown command returned unexpectedly"
log_message "=========================================="