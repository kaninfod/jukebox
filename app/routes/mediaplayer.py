from app.services.playback_manager import PlaybackManager
from fastapi import APIRouter, Body, Query
#from app.ui.screens import PlayerStatus
#import subprocess
#from typing import Dict, List, Union, Any




router = APIRouter()

def get_screen_manager():
    from app.main import screen_manager
    return screen_manager

@router.post("/mediaplayer/next_track")
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

@router.post("/mediaplayer/previous_track")
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

@router.post("/mediaplayer/play_pause")
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


@router.post("/mediaplayer/play")
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

@router.post("/mediaplayer/stop")
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



@router.post("/mediaplayer/volume_up")
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


@router.post("/mediaplayer/volume_down")
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


# Endpoint to trigger load_rfid in PlaybackManager
@router.post("/mediaplayer/playback_rfid")
def playbackmanager_load_rfid(rfid: str = Body(..., embed=True)):
    """Trigger load_rfid in PlaybackManager with the given RFID."""

    from app.core import event_bus, EventType, Event
    result = event_bus.emit(Event(
        type=EventType.RFID_READ,
        payload={"rfid": rfid}
    ))

    if result:
        return {"status": "success", "message": result}
    else:
        return {"status": "error", "message": "Failed to load RFID in PlaybackManager"}


# Endpoint to trigger load_from_audioPlaylistId in PlaybackManager
@router.post("/mediaplayer/playback_audioPlaylistId")
def playbackmanager_load_audioPlaylistId(audioPlaylistId: str = Body(..., embed=True), provider: str = Body("subsonic", embed=True)):
    """Trigger load_from_audioPlaylistId in PlaybackManager with the given audioPlaylistId."""
    
    try:
        from app.main import playback_manager
        result = playback_manager.load_from_audioPlaylistId(audioPlaylistId, provider)
        
        if result:
            return {
                "status": "success", 
                "message": f"Successfully loaded audioPlaylistId: {audioPlaylistId}",
                "audioPlaylistId": audioPlaylistId,
                "provider": provider
            }
        else:
            return {
                "status": "error", 
                "message": f"Failed to load audioPlaylistId: {audioPlaylistId}"
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Exception while loading audioPlaylistId {audioPlaylistId}: {str(e)}"
        }


# Endpoint to get all info on the current track from JukeboxMediaPlayer
@router.get("/mediaplayer/current_track")
def get_current_track_info():
    """Get all info on the current track from JukeboxMediaPlayer."""
    try:
        from app.main import playback_manager
        player = playback_manager.player if playback_manager else None
        if player and player.current_track:
            return {
                "artist": player.artist,
                "title": player.title,
                "duration": player.duration,
                "album": player.album,
                "year": player.year,
                "video_id": player.video_id,
                "track_number": player.track_number,
                "status": player.status.value
            }
        else:
            return {"status": "error", "message": "No track loaded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/mediaplayer/info")
def get_mediaplayer_info():
    """Get current media player information"""
    screen_manager = get_screen_manager()
    home_screen = screen_manager.screens.get('home')
    
    if home_screen:
        return {
            "current_screen": screen_manager.current_screen.name if screen_manager.current_screen else None,
            "volume": home_screen.volume,
            "status": home_screen.player_status.value,
            "track_info": {
                "artist": home_screen.artist_name,
                "album": home_screen.album_name,
                "year": home_screen.album_year,
                "track": home_screen.track_title,
                "image_url": home_screen.album_image_url
            }
        }
    
    return {"status": "No home screen available"}



