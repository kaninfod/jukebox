
from fastapi import APIRouter, Body, Query, WebSocket, WebSocketDisconnect
import asyncio
from app.config import config


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


@router.post("/api/mediaplayer/play")
def play():
    """Resume playback."""
    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.PLAY_PAUSE,
        payload={}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to start playback"}

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

    if result is not None:
        return {"status": "success", "volume": volume}
    else:
        return {"status": "error", "message": "Failed to set volume"}
    

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
def play_album_from_albumid(albumid: str):
    """Play album from album_id using PlaybackManager."""
    try:
        from app.core.service_container import get_service
        playback_service = get_service("playback_service")
        result = playback_service.load_from_album_id(albumid)
        if result:
            return {
                "status": "success",
                "message": f"Successfully loaded album_id: {albumid}",
                "album_id": albumid
            }
        else:
            return {
                "status": "error", 
                "message": f"Failed to load album_id: {albumid}"
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Exception while loading album_id {albumid}: {str(e)}"
        }

# Endpoint to get all info on the current track from JukeboxMediaPlayer
@router.get("/api/mediaplayer/current_track")
def get_current_track_info():
    """Get all info on the current track from JukeboxMediaPlayer."""
    try:
        return _get_data_for_current_track()
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Dedicated WebSocket route for current track updates (event-driven)
@router.websocket("/ws/mediaplayer/current_track")
async def websocket_current_track(websocket: WebSocket):
    await websocket.accept()
    import asyncio
    from app.core import event_bus, EventType
    from app.core.service_container import get_service

    q = asyncio.Queue()
    loop = asyncio.get_event_loop()
    handler_active = True

    def handler(event):
        # Called in event bus thread (may be non-async)
        try:
            data = _get_data_for_current_track()
            
            if handler_active:
                asyncio.run_coroutine_threadsafe(q.put(data), loop)
        except Exception as e:
            if handler_active:
                asyncio.run_coroutine_threadsafe(q.put({"status": "error", "message": str(e)}), loop)

    # Subscribe handler to TRACK_CHANGED
    event_bus.subscribe(EventType.TRACK_CHANGED, handler)
    event_bus.subscribe(EventType.VOLUME_CHANGED, handler)

    try:
        # Send initial state
        handler(None)
        while True:
            try:
                # Wait for new data from event handler (with timeout for ping)
                data = await asyncio.wait_for(q.get(), timeout=60)
                await websocket.send_json(data)
            except asyncio.TimeoutError:
                # Keep connection alive (ping)
                await websocket.send_json({"status": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        # Unsubscribe handler (cleanup)
        handler_active = False
        try:
            event_bus._handlers[EventType.TRACK_CHANGED].remove(handler)
        except Exception:
            pass
        try:
            event_bus._handlers[EventType.VOLUME_CHANGED].remove(handler)
        except Exception:
            pass


def _get_data_for_current_track():
    from app.core.service_container import get_service
    playback_service = get_service("playback_service")
    player = playback_service.player 
    if player and player.current_track:
        return {
            "current_track": {
                "artist": player.artist,
                "title": player.title,
                "duration": player.duration,
                "album": player.album,
                "year": player.year,
                "track_id": player.track_id,
                "track_number": player.track_number,
                "thumb": player.thumb,
                "thumb_abs": player.cc_cover_url
            },
            "status": player.status.value,
            "playlist": player.playlist,
            "volume": player.volume, 
            "chromecast_device": playback_service.player.cc_service.device_name
        }
    else:
        return {"status": "error", "message": "No track loaded"}

