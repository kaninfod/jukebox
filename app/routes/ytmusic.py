
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.ytmusic import YTMusicEntry, YTMusicEntryUpdate
from app.database import (
    create_ytmusic_entry,
    list_ytmusic_entries,
    get_ytmusic_entry_by_rfid,
    update_ytmusic_entry,
    delete_ytmusic_entry
)
from ytmusicapi import YTMusic, OAuthCredentials
import json



router = APIRouter()
ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id="194320065459-2854gle26f6899bg7mt1e579q0rvmnr1.apps.googleusercontent.com", client_secret="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"))





@router.get("/ytmusic", response_model=List[YTMusicEntry])
def list_ytmusic():
    return list_ytmusic_entries()

@router.get("/ytmusic/{rfid}", response_model=YTMusicEntry)
def get_ytmusic(rfid: str):
    entry = get_ytmusic_entry_by_rfid(rfid)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/ytmusic/{rfid}")
def create_ytmusic(rfid: str):
    return create_ytmusic_entry(rfid)

@router.put("/ytmusic/{rfid}/{audioPlaylistId}", response_model=YTMusicEntry)
def update_ytmusic(rfid: str, audioPlaylistId: str):
    # Get album info from YouTube Music
    try:
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        album_name = album_info.get('title', 'Unknown Album')
        artist_name = 'Unknown Artist'
        if album_info.get('artists') and len(album_info['artists']) > 0:
            artist_name = album_info['artists'][0].get('name', 'Unknown Artist')
        year = album_info.get('year', None)
        thumbnail = None
        thumbnails = album_info.get('thumbnails', [])
        for thumb in thumbnails:
            if thumb.get('width') == 120 and thumb.get('height') == 120:
                thumbnail = thumb.get('url')
                break
        tracks_data = []
        tracks = album_info.get('tracks', [])
        for track in tracks:
            track_info = {
                'title': track.get('title', 'Unknown Title'),
                'duration': track.get('duration', '0:00'),
                'track_number': track.get('trackNumber', 0),
                'video_id': track.get('videoId', '')
            }
            tracks_data.append(track_info)
        album_data = {
            'album_name': album_name,
            'artist_name': artist_name,
            'year': year,
            'yt_id': audioPlaylistId,
            'thumbnail': thumbnail,
            'tracks': json.dumps(tracks_data)
        }
        db_entry = update_ytmusic_entry(rfid, album_data)
        if not db_entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        return db_entry
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get album info: {str(e)}")

@router.delete("/ytmusic/{rfid}")
def delete_ytmusic(rfid: str):
    deleted = delete_ytmusic_entry(rfid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted"}


@router.get("/ytmusic/album_browse_id/{audioPlaylistId}")
def get_album(audioPlaylistId: str):
    try:
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        return album_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))