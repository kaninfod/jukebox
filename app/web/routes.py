
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import config
from app.routes.albums import list_album_entries_route, update_album_entry_route
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# NFC Encoding Status Page
@router.get("/nfc-encoding/status-page", response_class=HTMLResponse)
async def nfc_encoding_status_page(request: Request):
    return templates.TemplateResponse("nfc_encoding_status.html", {"request": request})


@router.get("/jukebox/albums", response_class=HTMLResponse)
async def albums(request: Request):
    # Call the Python API directly
    albums = list_album_entries_route()
    # If the result is a Response object, extract .body or .json()
    if hasattr(albums, 'body'):
        import json
        albums = json.loads(albums.body)
    return templates.TemplateResponse("albums.html", {"request": request, "albums": albums, "cover_path": "album_covers"})




# Subsonic: List all artists (fetch from JSON API)

@router.get("/subsonic/artists", response_class=HTMLResponse)
async def subsonic_artists(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:8000/api/subsonic/artists")
        resp.raise_for_status()
        artists = resp.json()
    return templates.TemplateResponse("subsonic_artists.html", {"request": request, "artists": artists})



# Subsonic: List albums for a given artist (fetch from JSON API)

@router.get("/subsonic/albums/{artist_id}", response_class=HTMLResponse)
async def subsonic_albums(request: Request, artist_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://127.0.0.1:8000/api/subsonic/artist/{artist_id}")
        resp.raise_for_status()
        albums = resp.json()
    return templates.TemplateResponse("subsonic_albums.html", {"request": request, "albums": albums, "artist_id": artist_id})

@router.post("/jukebox/albums/update_audioPlaylistId")
async def update_audioPlaylistId(rfid: str = Form(...), audioPlaylistId: str = Form(...), provider: str = Form(...)):
    # Call the Python API directly
    update_album_entry_route(rfid, audioPlaylistId)
    return RedirectResponse("/jukebox/albums", status_code=303)
