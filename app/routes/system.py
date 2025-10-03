
"""
System control routes for the jukebox.
Provides shutdown and reboot functionality.
"""
from fastapi import APIRouter, HTTPException
import logging
import subprocess
import asyncio
from typing import Dict
from app.config import config
from app.core import EventType, Event, event_bus
logger = logging.getLogger(__name__)

# --- Synchronous reboot logic for event handler ---
def reboot_system_sync():
    """
    Synchronous system reboot for use in event handlers or threads.
    """
    try:
        logger.info("(sync) System reboot requested via event handler.")
        result = subprocess.run(
            ["sudo", "systemctl", "reboot"],
            capture_output=True,
            text=True,
            timeout=config.SYSTEM_OPERATION_TIMEOUT
        )
        logger.info("(sync) System reboot command completed (should not happen if reboot works)")
    except subprocess.TimeoutExpired:
        logger.info("(sync) System reboot command timed out (expected if reboot works)")
    except Exception as e:
        logger.error(f"(sync) Failed to initiate reboot: {e}")

def _subscribe_reboot_event():
    def handle_reboot_event(event):
        logger.info("SYSTEM_REBOOT_REQUESTED event received, calling reboot_system_sync()")
        reboot_system_sync()
    event_bus.subscribe(EventType.SYSTEM_REBOOT_REQUESTED, handle_reboot_event)

_subscribe_reboot_event()


router = APIRouter(prefix="/api/system", tags=["system"])

@router.post("/shutdown")
async def shutdown_system() -> Dict[str, str]:
    """
    Shutdown the Raspberry Pi system.
    First gracefully shuts down the media player, then the system.
    Requires polkit rule to allow pi user to run systemctl poweroff.
    """
    try:
        # Step 1: Gracefully shutdown the media player first
        try:
            from app.routes.mediaplayer import shutdown_mediaplayer
            mediaplayer_result = await shutdown_mediaplayer()
            print(f"Mediaplayer shutdown result: {mediaplayer_result}")
        except Exception as e:
            print(f"Warning: Mediaplayer shutdown failed: {e}")
            # Continue with system shutdown even if mediaplayer shutdown fails
        
        # Step 2: Small delay to ensure mediaplayer shutdown completes
        await asyncio.sleep(config.SYSTEM_OPERATION_TIMEOUT / 2)
        
        # Step 3: Use systemctl poweroff for clean system shutdown
        # Note: This command typically doesn't return as the system shuts down
        result = subprocess.run(
            ["systemctl", "poweroff"], 
            capture_output=True, 
            text=True, 
            timeout=config.SYSTEM_OPERATION_TIMEOUT
        )
        
        # If we reach here, the command completed without shutdown
        return {"status": "success", "message": "System shutdown initiated (mediaplayer shutdown completed)"}
            
    except subprocess.TimeoutExpired:
        # Timeout is actually expected for poweroff
        return {"status": "success", "message": "System shutdown initiated (mediaplayer shutdown completed)"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initiate shutdown: {str(e)}"
        )

@router.post("/reboot")
async def reboot_system() -> Dict[str, str]:
    """
    Reboot the Raspberry Pi system.
    Requires polkit rule to allow pi user to run systemctl reboot.
    """
    try:
        # Use systemctl reboot for clean restart
        # Note: This command typically doesn't return as the system reboots
        result = subprocess.run(
            ["sudo", "/usr/bin/systemctl", "reboot"],
            capture_output=True, 
            text=True, 
            timeout=config.SYSTEM_OPERATION_TIMEOUT
        )
        
        # If we reach here, the command completed without reboot
        return {"status": "success", "message": "System reboot initiated"}
            
    except subprocess.TimeoutExpired:
        # Timeout is actually expected for reboot
        return {"status": "success", "message": "System reboot initiated"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initiate reboot: {str(e)}"
        )

@router.get("/status")
async def system_status() -> Dict[str, str]:
    """
    Get basic system status information.
    """
    try:
        # Get uptime
        uptime_result = subprocess.run(
            ["uptime", "-p"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        # Get hostname
        hostname_result = subprocess.run(
            ["hostname"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        return {
            "status": "online",
            "uptime": uptime_result.stdout.strip() if uptime_result.returncode == 0 else "unknown",
            "hostname": hostname_result.stdout.strip() if hostname_result.returncode == 0 else "unknown"
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to get system status: {str(e)}"
        }

from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@router.get("/metrics")
async def metrics_endpoint():
    """
    Expose Prometheus metrics for scraping.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)