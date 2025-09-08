from pydantic import BaseModel, validator
from typing import Optional, List
import json

class Track(BaseModel):
    title: str
    duration: str
    track_number: int
    video_id: str

class AlbumEntry(BaseModel):
    rfid: str
    provider: Optional[str] = "youtube_music"
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    audioPlaylistId: Optional[str] = None
    thumbnail: Optional[str] = None
    tracks: Optional[List[Track]] = None
    
    @validator('tracks', pre=True)
    def parse_tracks_json(cls, v):
        if isinstance(v, str):
            try:
                tracks_data = json.loads(v)
                return [Track(**track) for track in tracks_data]
            except (json.JSONDecodeError, TypeError):
                return None
        return v
    
    class Config:
        orm_mode = True

class AlbumEntryUpdate(BaseModel):
    provider: Optional[str] = None
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    audioPlaylistId: Optional[str] = None
    thumbnail: Optional[str] = None
    tracks: Optional[List[Track]] = None
