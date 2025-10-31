from fastapi import APIRouter, HTTPException, Response
from fastapi import Query
from app.core.service_container import get_service


router = APIRouter()

@router.get("/api/subsonic/artists")
def get_all_artists():
    """Return all artists from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    artists = subsonic_service.list_artists()
    if artists is None:
        raise HTTPException(status_code=404, detail="No artists found")
    return artists

@router.get("/api/subsonic/artist/{id}")
def get_artist_albums(id: str):
    """Return all albums by artist (id) from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    albums = subsonic_service.list_albums_for_artist(id)
    if albums is None:
        raise HTTPException(status_code=404, detail="No albums found for artist")
    return albums

@router.get("/api/subsonic/album/{id}")
def get_album_songs(id: str):
    """Return all songs on album (id) from SubsonicService."""
    subsonic_service = get_service("subsonic_service")
    songs = subsonic_service.get_album_tracks(id)
    if songs is None:
        raise HTTPException(status_code=404, detail="No songs found for album")
    return songs

@router.get("/api/subsonic/cover/{album_id}")
def get_cover_art(album_id: str):
    """
    Proxy cover art through the jukebox API so the browser doesn't need
    credentials for the Gonic host. Uses SubsonicService with optional
    proxy Basic auth configured in ENV.
    """
    subsonic_service = get_service("subsonic_service")
    try:
        resp = subsonic_service._api_request("getCoverArt", {"id": album_id})
        content_type = resp.headers.get("Content-Type", "image/png")
        return Response(content=resp.content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch cover art: {e}")

@router.get("/api/subsonic/album_info/{id}")
def get_album_info(id: str):
    """Return album metadata (name, artist, etc.) for the given album id."""
    subsonic_service = get_service("subsonic_service")
    try:
        album = subsonic_service.get_album_info(id)
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
        return album
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch album info: {e}")


@router.get("/api/images/covers/{album_id}")
def get_cover_static_url(album_id: str, size: int = Query(180, ge=64, le=1024), absolute: bool = Query(False)):
    """
    Return the static cover URL for a given album id and size. Ensures generation if missing.
    """
    subsonic_service = get_service("subsonic_service")
    try:
        url = subsonic_service.get_cover_static_url(album_id, size=size, absolute=absolute)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to resolve cover URL: {e}")
