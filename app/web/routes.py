

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import config
import httpx
import asyncio

# Internal API access settings
LOCAL_API_BASE = "http://127.0.0.1:8000"
# Tell the app that original scheme is HTTPS to avoid HTTP->HTTPS redirect on loopback,
# and include API key for protected /api/* endpoints (bypass NPM injection on loopback)
FORWARDED_HEADERS = {"X-Forwarded-Proto": "https"}
if getattr(config, "API_KEY", None):
    FORWARDED_HEADERS["X-API-Key"] = config.API_KEY

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# New unified routes

# /status: Media player status page (was /mediaplayer/status)
@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    return templates.TemplateResponse("mediaplayer_status.html", {"request": request})

# /nfc: NFC encoding status page (was /nfc-encoding/status-page)
@router.get("/nfc", response_class=HTMLResponse)
async def nfc_status(request: Request):
    return templates.TemplateResponse("nfc_encoding_status.html", {"request": request})

# /albums: Local Jukebox album catalog (was /jukebox/albums)
@router.get("/albums", response_class=HTMLResponse)
async def albums(request: Request):
    # Fetch base mappings from API
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOCAL_API_BASE}/api/albums",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        entries = resp.json()

        # Concurrently fetch album info for each album_id
        async def fetch_info(album_id: str):
            if not album_id:
                return {"name": "", "artist": ""}
            r = await client.get(
                f"{LOCAL_API_BASE}/api/subsonic/album_info/{album_id}",
                headers=FORWARDED_HEADERS,
                follow_redirects=True,
            )
            if r.status_code == 200:
                return r.json()
            return {"name": "", "artist": ""}

        tasks = [fetch_info(e.get("album_id") if isinstance(e, dict) else getattr(e, "album_id", None)) for e in entries]
        infos = await asyncio.gather(*tasks)

    enriched = []
    for entry, info in zip(entries, infos):
        if hasattr(entry, 'rfid') and hasattr(entry, 'album_id'):
            rfid = entry.rfid
            album_id = entry.album_id
        else:
            rfid = entry.get('rfid') if isinstance(entry, dict) else None
            album_id = entry.get('album_id') if isinstance(entry, dict) else None

        enriched.append({
            "rfid": rfid,
            "album_id": album_id,
            "album_name": (info or {}).get("name", ""),
            "artist_name": (info or {}).get("artist", ""),
            "cover_url": f"/api/subsonic/cover/{album_id}" if album_id else None,
        })

    return templates.TemplateResponse(
        "albums.html",
        {"request": request, "albums": enriched}
    )

# /library: Subsonic browsing entry (redirect to /library/artists)
@router.get("/library")
async def library_root():
    return RedirectResponse(url="/library/artists", status_code=308)

# /library/artists: Subsonic artists list (was /subsonic/artists)
@router.get("/library/artists", response_class=HTMLResponse)
async def library_artists(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOCAL_API_BASE}/api/subsonic/artists",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        artists = resp.json()
    return templates.TemplateResponse("subsonic_artists.html", {"request": request, "artists": artists})

# /library/artists/{artist_id}: Albums for artist (was /subsonic/albums/{artist_id})
@router.get("/library/artists/{artist_id}", response_class=HTMLResponse)
async def library_artist_albums(request: Request, artist_id: str, artist_name: str = None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOCAL_API_BASE}/api/subsonic/artist/{artist_id}",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        albums = resp.json()
    return templates.TemplateResponse("subsonic_albums.html", {"request": request, "albums": albums, "artist_id": artist_id, "artist_name": artist_name})

# /library/albums/{album_id}: Songs for album (was /subsonic/album/{album_id})
@router.get("/library/albums/{album_id}", response_class=HTMLResponse)
async def library_album_songs(request: Request, album_id: str, artist_id: str = None, artist_name: str = None, album_name: str = None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOCAL_API_BASE}/api/subsonic/album/{album_id}",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        songs = resp.json()
    return templates.TemplateResponse("subsonic_album_songs.html", {"request": request, "songs": songs, "album_id": album_id, "artist_id": artist_id, "artist_name": artist_name, "album_name": album_name})

# Back-compat redirects from old paths to unified ones

@router.get("/mediaplayer/status")
async def redirect_old_status():
    return RedirectResponse(url="/status", status_code=308)

@router.get("/nfc-encoding/status-page")
async def redirect_old_nfc():
    return RedirectResponse(url="/nfc", status_code=308)


@router.get("/jukebox/albums")
async def redirect_old_albums():
    return RedirectResponse(url="/albums", status_code=308)




# Subsonic: List all artists (fetch from JSON API)

@router.get("/subsonic/artists")
async def redirect_old_artists():
    return RedirectResponse(url="/library/artists", status_code=308)



# Subsonic: List albums for a given artist (fetch from JSON API)


# Subsonic: List albums for a given artist (fetch from JSON API)
@router.get("/subsonic/albums/{artist_id}")
async def redirect_old_artist_albums(artist_id: str, request: Request):
    qs = str(request.url.query)
    dest = f"/library/artists/{artist_id}"
    if qs:
        dest += f"?{qs}"
    return RedirectResponse(url=dest, status_code=308)

# Subsonic: List songs for a given album (fetch from JSON API)
@router.get("/subsonic/album/{album_id}")
async def redirect_old_album_songs(album_id: str, request: Request):
    qs = str(request.url.query)
    dest = f"/library/albums/{album_id}"
    if qs:
        dest += f"?{qs}"
    return RedirectResponse(url=dest, status_code=308)

@router.post("/albums/update")
async def update_album_mapping(rfid: str = Form(...), audioPlaylistId: str = Form(...), provider: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{LOCAL_API_BASE}/api/albums/{rfid}/{audioPlaylistId}",
            headers=FORWARDED_HEADERS,
        )
        resp.raise_for_status()
    return RedirectResponse("/albums", status_code=303)

@router.post("/jukebox/albums/update_audioPlaylistId")
async def update_audioPlaylistId(rfid: str = Form(...), audioPlaylistId: str = Form(...), provider: str = Form(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{LOCAL_API_BASE}/api/albums/{rfid}/{audioPlaylistId}",
            headers=FORWARDED_HEADERS,
        )
        resp.raise_for_status()
    return RedirectResponse("/albums", status_code=303)
