from app.services.playback_manager import PlaybackManager
from fastapi import APIRouter, Body, Query
from app.ui.screens import PlayerStatus
import subprocess
from typing import Dict, List, Union, Any
from app.routes.homeassistant import stop_ytube_music_player
from app.services.websocket_client import stop_websocket



router = APIRouter()

def get_screen_manager():
    from app.main import screen_manager
    return screen_manager

@router.post("/mediaplayer/next_track")
def next_track():
    """Advance to the next track."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.next_track()
            return {"status": "success", "message": "Advanced to next track"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/mediaplayer/previous_track")
def previous_track():
    """Go to the previous track."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.previous_track()
            return {"status": "success", "message": "Went to previous track"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/mediaplayer/play_pause")
def play_pause():
    """Toggle playback."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.play_pause()
            return {"status": "success", "message": "Toggled playback"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/mediaplayer/play")
def play():
    """Resume playback."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.play()
            return {"status": "success", "message": "Resumed playback"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/mediaplayer/stop")
def stop():
    """Stop playback."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.stop()
            return {"status": "success", "message": "Stopped playback"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/mediaplayer/volume_up")
def volume_up():
    """Increase volume using JukeboxMediaPlayer (master of volume, syncs to HA)."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.volume_up()
            return {"status": "success", "message": "Volume increased"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/mediaplayer/volume_down")
def volume_down():
    """Decrease volume using JukeboxMediaPlayer (master of volume, syncs to HA)."""
    try:
        from app.main import playback_manager
        if playback_manager and playback_manager.player:
            playback_manager.player.volume_down()
            return {"status": "success", "message": "Volume decreased"}
        else:
            return {"status": "error", "message": "No player available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Endpoint to trigger load_rfid in PlaybackManager
@router.post("/mediaplayer/playback_rfid")
def playbackmanager_load_rfid(rfid: str = Body(..., embed=True)):
    """Trigger load_rfid in PlaybackManager with the given RFID."""
    try:
        from app.main import playback_manager
        result = playback_manager.load_rfid(rfid)
        if result:
            return {"status": "success", "message": f"RFID {rfid} loaded in PlaybackManager"}
        else:
            return {"status": "error", "message": f"Failed to load RFID {rfid} in PlaybackManager"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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


