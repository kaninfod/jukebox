"""
WebSocket client for Home Assistant integration.
Handles real-time state updates from Home Assistant.
"""


import json
import asyncio
import websockets
import threading
import signal
from typing import Any, Dict, Optional
from app.config import config
import logging
import asyncio
from app.services.jukebox_mediaplayer import JukeboxMediaPlayer, PlayerStatus
logger = logging.getLogger(__name__)

# WebSocket connection state
websocket_connection = None
websocket_task = None
is_websocket_running = False
websocket_lock = threading.Lock()

# Signal handler for graceful shutdown
def _signal_handler(signum, frame):
    logger.info(f"WebSocket: Received signal {signum}, shutting down...")
    stop_websocket()

# Register signal handlers
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


_advance_task = None  # Debounce task for advancing track

async def _debounced_advance_next_track():
    await asyncio.sleep(1)  # 1 second debounce
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.next_track()
            logger.info("Advanced to next track after debounce.")
    except Exception as e:
        logger.warning(f"Debounced advance failed: {e}")

async def handle_state_change(event_data: Dict[str, Any]) -> None:
    """Handle state change events from Home Assistant WebSocket (only state changes)."""
    try:
        # Check if this is the media player we're interested in
        entity_id = event_data.get("entity_id")
        media_player_entity_id = getattr(config, "MEDIA_PLAYER_ENTITY_ID", None)
        if entity_id != media_player_entity_id:
            return

        new_state = event_data.get("new_state", {})
        old_state = event_data.get("old_state", {})
        state = new_state.get("state", "idle")
        old_status = old_state.get("state", None)

        # Only act if the state value actually changed
        if state == old_status:
            return

        logger.info(f"WebSocket: Media player state changed to: {state}")

        # Map HA state to PlayerStatus enum
        status_map = {
            "playing": PlayerStatus.PLAY,
            "paused": PlayerStatus.PAUSE,
            "idle": PlayerStatus.STOP,
            "unavailable": PlayerStatus.STANDBY,
            "off": PlayerStatus.OFF
        }
        player_status = status_map.get(state, PlayerStatus.STOP)

        # Update the JukeboxMediaPlayer status using the global playback_manager
        global _advance_task
        try:
            from app.main import playback_manager
            if playback_manager and playback_manager.player:
                playback_manager.player.status = player_status
                logger.info(f"Updated JukeboxMediaPlayer status to {player_status.value}")
                # Debounced advance to next track if state changed from playing to idle
                if old_status == "playing" and state == "idle":
                    # Cancel any previous debounce
                    if _advance_task and not _advance_task.done():
                        _advance_task.cancel()
                    loop = asyncio.get_event_loop()
                    _advance_task = loop.create_task(_debounced_advance_next_track())
                elif state == "playing":
                    # Cancel debounce if playback resumes
                    if _advance_task and not _advance_task.done():
                        _advance_task.cancel()
        except Exception as e:
            logger.warning(f"Could not update JukeboxMediaPlayer status: {e}")
    except Exception as e:
        logger.error(f"WebSocket: Error handling state change: {e}")


async def websocket_client() -> None:
    backoff = 1
    max_backoff = 60
    global websocket_connection, is_websocket_running
    while True:
        try:
            logger.info("WebSocket: Connecting to Home Assistant...")
            async with websockets.connect(config.HA_WS_URL) as websocket:
                with websocket_lock:
                    websocket_connection = websocket
                    is_websocket_running = True
                
                # Step 1: Receive auth_required message
                auth_required = await websocket.recv()
                logger.debug(f"WebSocket: {auth_required}")
                
                # Step 2: Send authentication
                auth_message = {
                    "type": "auth",
                    "access_token": config.HA_TOKEN
                }
                await websocket.send(json.dumps(auth_message))
                
                # Step 3: Receive auth_ok
                auth_response = await websocket.recv()
                logger.debug(f"WebSocket: {auth_response}")
                
                # Step 4: Subscribe to state_changed events for our entity
                subscribe_message = {
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed"
                }
                await websocket.send(json.dumps(subscribe_message))
                
                # Step 5: Receive subscription confirmation
                subscribe_response = await websocket.recv()
                logger.debug(f"WebSocket: {subscribe_response}")
                
                logger.info("WebSocket: Connected and subscribed to state changes")
                
                # Step 6: Listen for events
                async for message in websocket:
                    # Check if we should stop (for graceful shutdown)
                    if not is_websocket_running:
                        logger.info("WebSocket: Shutdown requested, stopping message loop")
                        break
                        
                    try:
                        data = json.loads(message)
                        
                        # Check if this is a state_changed event
                        if (data.get("type") == "event" and 
                            data.get("event", {}).get("event_type") == "state_changed"):
                            
                            event_data = data.get("event", {}).get("data", {})
                            await handle_state_change(event_data)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"WebSocket: Invalid JSON received: {message}")
                    except Exception as e:
                        logger.error(f"WebSocket: Error processing message: {e}")
        
        except Exception as e:
            logger.error(f"WebSocket: Connection error: {e}")
            logger.info(f"WebSocket: Reconnecting in {backoff} seconds...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            with websocket_lock:
                is_websocket_running = False
                websocket_connection = None
            logger.info("WebSocket: Disconnected")
        if not is_websocket_running:
            break


def start_websocket_background() -> bool:
    """Start WebSocket client in background thread"""
    def run_websocket():
        asyncio.new_event_loop().run_until_complete(websocket_client())
    
    global websocket_task
    if not is_websocket_running:
        websocket_task = threading.Thread(target=run_websocket, daemon=True)
        websocket_task.start()
        return True
    return False


def start_websocket() -> Dict[str, str]:
    """Start WebSocket connection to Home Assistant"""
    try:
        if is_websocket_running:
            return {"status": "already_running", "message": "WebSocket is already connected"}
        
        success = start_websocket_background()
        if success:
            return {"status": "starting", "message": "WebSocket connection initiated"}
        else:
            return {"status": "failed", "message": "Failed to start WebSocket"}
            
    except Exception as e:
        return {"status": "error", "message": f"Failed to start WebSocket: {str(e)}"}


def websocket_status() -> Dict[str, Any]:
    """Get WebSocket connection status"""
    with websocket_lock:
        return {
            "is_running": is_websocket_running,
            "connection_active": websocket_connection is not None
        }


def stop_websocket() -> Dict[str, str]:
    """Stop WebSocket connection"""
    global is_websocket_running, websocket_connection, websocket_task
    logger.info("Stopping WebSocket connection...")
    with websocket_lock:
        is_websocket_running = False
        websocket_connection = None
    import time
    time.sleep(0.1)
    return {"status": "stopped", "message": "WebSocket connection terminated"}
