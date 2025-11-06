#!/bin/bash
# Script to perform jukebox service restart
# This script is called by cron when a restart trigger is detected

# Set PATH explicitly for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Logging function
log_message() {
    echo "$(date): do_restart.sh: $1" | tee -a /home/pi/shared/jukebox/tmp/restart.log
}

log_message "=========================================="
log_message "Jukebox service restart script started"
log_message "=========================================="

# Log environment info
log_message "User: $(whoami)"
log_message "PWD: $PWD"
log_message "PATH: $PATH"

# Execute jukebox service restart
log_message "Executing jukebox service restart command..."
log_message "Command: sudo /usr/bin/systemctl restart jukebox"

# Execute the restart command
sudo /usr/bin/systemctl restart jukebox

# Check the result
if [ $? -eq 0 ]; then
    log_message "SUCCESS: Jukebox service restart command executed successfully"
else
    log_message "ERROR: Jukebox service restart command failed with exit code $?"
fi

log_message "=========================================="