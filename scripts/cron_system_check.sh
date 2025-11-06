#!/bin/bash
# Cron script to check for system operation triggers and execute appropriate actions
# This runs every minute via cron and handles reboot, shutdown, and other system operations

# Set PATH explicitly for cron environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Set working directory
cd /home/pi

TRIGGER_DIR="/home/pi/shared/jukebox/tmp"
REBOOT_TRIGGER="$TRIGGER_DIR/reboot_trigger"
SHUTDOWN_TRIGGER="$TRIGGER_DIR/shutdown_trigger"
RESTART_TRIGGER="$TRIGGER_DIR/restart_trigger"
REBOOT_SCRIPT="/home/pi/shared/jukebox/scripts/do_reboot.sh"
SHUTDOWN_SCRIPT="/home/pi/shared/jukebox/scripts/do_shutdown.sh"
RESTART_SCRIPT="/home/pi/shared/jukebox/scripts/do_restart.sh"
CRON_LOG="$TRIGGER_DIR/cron.log"

# Logging function
log_message() {
    echo "$(date): cron_system_check: $1" >> "$CRON_LOG"
}

# Check for reboot trigger
if [ -f "$REBOOT_TRIGGER" ]; then
    log_message "=========================================="
    log_message "Reboot trigger detected, executing reboot script"
    log_message "Trigger file: $REBOOT_TRIGGER"
    log_message "Reboot script: $REBOOT_SCRIPT"
    log_message "Script exists: $([ -f "$REBOOT_SCRIPT" ] && echo 'YES' || echo 'NO')"
    log_message "Script executable: $([ -x "$REBOOT_SCRIPT" ] && echo 'YES' || echo 'NO')"
    
    # Remove trigger file first
    rm -f "$REBOOT_TRIGGER"
    
    # Execute reboot script
    log_message "Executing reboot script..."
    /bin/bash "$REBOOT_SCRIPT" >> "$CRON_LOG" 2>&1
    
    # If we reach here, reboot failed
    log_message "ERROR: Reboot script returned unexpectedly"
    log_message "=========================================="

# Check for shutdown trigger
elif [ -f "$SHUTDOWN_TRIGGER" ]; then
    log_message "=========================================="
    log_message "Shutdown trigger detected, executing shutdown script"
    log_message "Trigger file: $SHUTDOWN_TRIGGER"
    log_message "Shutdown script: $SHUTDOWN_SCRIPT"
    log_message "Script exists: $([ -f "$SHUTDOWN_SCRIPT" ] && echo 'YES' || echo 'NO')"
    log_message "Script executable: $([ -x "$SHUTDOWN_SCRIPT" ] && echo 'YES' || echo 'NO')"
    
    # Remove trigger file first
    rm -f "$SHUTDOWN_TRIGGER"
    
    # Execute shutdown script
    log_message "Executing shutdown script..."
    /bin/bash "$SHUTDOWN_SCRIPT" >> "$CRON_LOG" 2>&1
    
    # If we reach here, shutdown failed
    log_message "ERROR: Shutdown script returned unexpectedly"
    log_message "=========================================="

# Check for restart trigger
elif [ -f "$RESTART_TRIGGER" ]; then
    log_message "=========================================="
    log_message "Restart trigger detected, executing restart script"
    log_message "Trigger file: $RESTART_TRIGGER"
    log_message "Restart script: $RESTART_SCRIPT"
    log_message "Script exists: $([ -f "$RESTART_SCRIPT" ] && echo 'YES' || echo 'NO')"
    log_message "Script executable: $([ -x "$RESTART_SCRIPT" ] && echo 'YES' || echo 'NO')"
    
    # Remove trigger file first
    rm -f "$RESTART_TRIGGER"
    
    # Execute restart script
    log_message "Executing restart script..."
    /bin/bash "$RESTART_SCRIPT" >> "$CRON_LOG" 2>&1
    
    # Log completion (restart doesn't terminate the script)
    log_message "Restart script completed with exit code: $?"
    log_message "=========================================="

# If no triggers found, just exit silently (no logging needed for normal case)
fi