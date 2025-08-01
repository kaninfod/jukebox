from pydantic import BaseModel, validator
from typing import Optional, List
import json

class Track(BaseModel):
    title: str
    duration: str
    track_number: int
    video_id: str

class YTMusicEntry(BaseModel):
    rfid: str
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    yt_id: Optional[str] = None
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
        from_attributes = True

class YTMusicEntryUpdate(BaseModel):
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    yt_id: Optional[str] = None
    thumbnail: Optional[str] = None
    tracks: Optional[List[Track]] = None
