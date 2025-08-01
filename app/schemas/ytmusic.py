from pydantic import BaseModel
from typing import Optional

class YTMusicEntry(BaseModel):
    rfid: str
    album_name: str
    artist_name: str
    year: int
    yt_id: str
    class Config:
        from_attributes = True

class YTMusicEntryUpdate(BaseModel):
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    yt_id: Optional[str] = None
