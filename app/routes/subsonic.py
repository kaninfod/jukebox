from fastapi import APIRouter, HTTPException
from app.core.service_container import get_service

router = APIRouter()

@router.get("/subsonic/artists")
def get_all_artists():
    """Return all artists from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    artists = subsonic_service.get_all_artists()
    if artists is None:
        raise HTTPException(status_code=404, detail="No artists found")
    return artists

@router.get("/subsonic/artist/{id}")
def get_artist_albums(id: str):
    """Return all albums by artist (id) from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    albums = subsonic_service.get_albums_by_artist(id)
    if albums is None:
        raise HTTPException(status_code=404, detail="No albums found for artist")
    return albums

@router.get("/subsonic/album/{id}")
def get_album_songs(id: str):
    """Return all songs on album (id) from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    songs = subsonic_service.get_songs_by_album(id)
    if songs is None:
        raise HTTPException(status_code=404, detail="No songs found for album")
    return songs
