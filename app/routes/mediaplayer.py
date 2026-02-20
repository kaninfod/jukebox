
from fastapi import APIRouter, Body, Query, WebSocket, WebSocketDisconnect
import asyncio
from app.config import config
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# def get_screen_manager():
#     from app.core.service_container import get_service
#     return get_service("screen_manager")

# Helper: build absolute URL for thumbs using PUBLIC_BASE_URL when a relative path is provided
def _abs_url(url: str):
    if not url:
        return url
    if isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
        return url
    base = getattr(config, "PUBLIC_BASE_URL", "").rstrip("/")
    return f"{base}{url}" if base else url

@router.post("/api/mediaplayer/previous_track")
def previous_track():
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.PREVIOUS_TRACK,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to go to previous track"}

@router.post("/api/mediaplayer/next_track")
def next_track():
    """Advance to the next track."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.NEXT_TRACK,
        payload={"force": True}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to advance to next track"}
    
@router.post("/api/mediaplayer/play_track")
def play_track(track_index: int = Body(..., embed=True)):
    """Play a specific track by index in the current playlist."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.PLAY_TRACK,
        payload={"track_index": track_index}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": f"Failed to play track at index {track_index}"}

    

@router.post("/api/mediaplayer/play_pause")
def play_pause():
    """Toggle playback."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.PLAY_PAUSE,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to toggle playback"}

@router.post("/api/mediaplayer/stop")
def stop():
    """Stop playback."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.STOP,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to stop playback"}



@router.post("/api/mediaplayer/volume_up")
def volume_up():
    """Increase volume using JukeboxMediaPlayer (master of volume, syncs to HA)."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.VOLUME_UP,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to increase volume"}


@router.post("/api/mediaplayer/volume_down")
def volume_down():
    """Decrease volume using JukeboxMediaPlayer (master of volume, syncs to HA)."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.VOLUME_DOWN,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to decrease volume"}


@router.post("/api/mediaplayer/volume_set")
def volume_set(volume: int = Query(..., ge=0, le=100)):
    """Set volume to an explicit level (0-100) via event bus."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.SET_VOLUME,
        payload={"volume": volume}
    ))
    
    logger.debug(f"Volume set event result: {result}")
    
    if result is not None:
        return {"status": "success", "volume": volume}
    else:
        return {"status": "error", "message": "Failed to set volume"}


@router.post("/api/mediaplayer/volume_mute")
def volume_mute():
    """Toggle mute on the Chromecast device."""
    from app.core import event_bus, EventType, Event
    
    result = event_bus.emit(Event(
        type=EventType.VOLUME_MUTE,
        payload={}
    ))
    
    logger.debug(f"Volume mute event result: {result}")
    
    if result and len(result) > 0:
        mute_result = result[0]
        if isinstance(mute_result, dict) and mute_result.get("success"):
            muted = mute_result.get("muted")
            return {
                "status": "success", 
                "message": f"Volume {'muted' if muted else 'unmuted'}",
                "muted": muted
            }
    
    return {"status": "error", "message": "Failed to toggle mute"}
    

@router.post("/api/mediaplayer/toggle_repeat_album")
def toggle_repeat_album():
    """Toggle repeat album mode in PlaybackManager."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.TOGGLE_REPEAT_ALBUM,
        payload={}
    ))
    
    logger.debug(f"Toggle repeat album event result: {result}")

    if result is not None:
        return {"status": "success", "repeat_album": result}
    else:
        return {"status": "error", "message": "Failed to toggle repeat album mode"}


@router.get("/api/mediaplayer/output_readiness")
def output_readiness():
    """Inspect active playback backend and output readiness (including BT for MPV)."""
    try:
        from app.core.service_container import get_service

        player = get_service("media_player_service")
        backend = getattr(player, "playback_backend", None)

        if not backend:
            return {"status": "error", "message": "No playback backend available"}

        backend_name = type(backend).__name__
        status = backend.get_status() if hasattr(backend, "get_status") else None
        readiness = (
            backend.get_output_readiness()
            if hasattr(backend, "get_output_readiness")
            else {"ready": True, "message": "No backend-specific output readiness checks"}
        )

        return {
            "status": "ok",
            "backend": backend_name,
            "device_name": getattr(backend, "device_name", None),
            "backend_status": status,
            "output_readiness": readiness,
        }
    except Exception as e:
        logger.error(f"Failed to inspect output readiness: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/api/mediaplayer/play_album_from_rfid/{rfid}")
def play_album_from_rfid(rfid: str):
    """Play album from RFID using PlaybackManager."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.RFID_READ,
        payload={"rfid": rfid}
    ))
    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to load RFID in PlaybackManager"}


# Endpoint to trigger load_from_album_id in PlaybackManager


@router.post("/api/mediaplayer/play_album_from_albumid/{albumid}")
def play_album_from_albumid(albumid: str, start_track_index: int = Query(0, ge=0)):
    """Play album from album_id using PlaybackManager.
    
    Args:
        albumid: The album ID to play
        start_track_index: Optional track index to start playback from (default: 0)
    """
    try:
        from app.core.service_container import get_service
        playback_service = get_service("playback_service")
        result = playback_service.load_from_album_id(albumid, start_track_index=start_track_index)
        if result:
            return {
                "status": "success",
                "message": f"Successfully loaded album_id: {albumid} (starting at track {start_track_index})",
                "album_id": albumid,
                "start_track_index": start_track_index
            }
        else:
            return {
                "status": "error", 
                "message": f"Failed to load album_id: {albumid}"
            }
    except Exception as e:
        logger.error(f"Exception while loading album_id {albumid}: {e}")
        return {
            "status": "error", 
            "message": f"Exception while loading album_id {albumid}: {str(e)}"
        }

# Endpoint to get all info on the current track from JukeboxMediaPlayer
@router.get("/api/mediaplayer/status")
def get_current_track_info():
    """Get all info on the current track from JukeboxMediaPlayer.

    Kept function name for backwards compatibility; endpoint moved to
    /api/mediaplayer/status.
    """
    try:
        payload = _get_data_for_current_track()
        #logger.debug("status payload: %s", payload)
        return  {"type": "current_track", "payload": payload}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Dedicated WebSocket route for current track updates (event-driven)
@router.websocket("/ws/mediaplayer/status")
async def websocket_status(websocket: WebSocket):
    """Multipurpose websocket for publishing typed status messages.

    This handler wires per-connection asyncio queue and registers
    event-bus handlers created by `_make_ws_handlers` below. Handlers
    are kept small and pluggable so new event types can be added
    without changing the connection scaffolding.
    """
    await websocket.accept()
    from app.core import event_bus, EventType
    from app.core.service_container import get_service

    q = asyncio.Queue()
    loop = asyncio.get_event_loop()
    handler_active = {"active": True}

    # Create per-connection handlers for events we care about.
    handlers = _make_ws_handlers(q, loop, handler_active)

    # Subscribe all handlers
    for evt_type, h in handlers.items():
        event_bus.subscribe(evt_type, h)

    try:
        # Send an initial state by invoking the track handler if present
        if EventType.TRACK_CHANGED in handlers:
            handlers[EventType.TRACK_CHANGED](None)

        while True:
            try:
                message = await asyncio.wait_for(q.get(), timeout=60)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                # Keep connection alive (ping)
                await websocket.send_json({"type": "ping", "payload": {}})
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        logger.info("WebSocket status handler cancelled during shutdown")
        return
    finally:
        # Unsubscribe and cleanup
        handler_active["active"] = False
        for evt_type, h in handlers.items():
            try:
                event_bus._handlers[evt_type].remove(h)
            except Exception:
                pass

def _make_ws_handlers(q: "asyncio.Queue", loop, handler_active: dict):
    """Factory for per-connection websocket handlers.

    Returns a mapping of EventType -> callable(event).
    Handlers will schedule messages onto the provided queue.
    """
    import asyncio
    from app.core import EventType

    def _push_message(message):
        if handler_active.get("active"):
            asyncio.run_coroutine_threadsafe(q.put(message), loop)

    def track_handler(event):
        try:
            # If event is None (we invoke handler to send initial state),
            # build payload from the current player state. Otherwise use the
            # event.payload provided by the event bus.
            if event is None:
                payload = _get_data_for_current_track()
            else:
                payload = getattr(event, 'payload', None) or _get_data_for_current_track()
            message = {"type": "current_track", "payload": payload}
            #logger.debug(f"Track changed event: {message}")
            _push_message(message)
        except Exception as e:
            _push_message({"type": "error", "payload": {"message": str(e)}})

    def volume_handler(event):
        try:
            # For volume changes we send the full status payload so clients
            # have a consistent view. Could be optimized to send only delta.
            payload = _get_data_for_current_track()
            message = {"type": "volume_changed", "payload": payload}
            logger.debug(f"Volume changed event: {message}")
            _push_message(message)
        except Exception as e:
            _push_message({"type": "error", "payload": {"message": str(e)}})

    def notification_handler(event):
        try:
            payload = event.payload
            message = {"type": "notification", "payload": payload}
            logger.debug(f"Notification event: {message}")
            _push_message(message)
        except Exception as e:
            _push_message({"type": "error", "payload": {"message": str(e)}})

    return {
        EventType.TRACK_CHANGED: track_handler,
        EventType.VOLUME_CHANGED: track_handler,
        EventType.NOTIFICATION: notification_handler,
    }

def _get_data_for_current_track():
    from app.core.service_container import get_service
    playback_service = get_service("playback_service")
    player = playback_service.player 
    return player.get_context()