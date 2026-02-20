from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import config
from app.core.service_container import get_service
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
async def status_page(request: Request, kiosk: bool = False):
    if kiosk:
        return templates.TemplateResponse("pages/kiosk/player.html", {
            "request": request,
            "kiosk_mode": True,
            "config": config
        })
    else:
        return templates.TemplateResponse("pages/desktop/player.html", {
            "request": request,
            "kiosk_mode": False,
            "config": config
        })

# /nfc: NFC encoding status page (was /nfc-encoding/status-page)
@router.get("/nfc", response_class=HTMLResponse)
async def nfc_status(request: Request):
    return templates.TemplateResponse("nfc_encoding_status.html", {"request": request, "config": config})

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
    subsonic_service = get_service("subsonic_service")
    for entry, info in zip(entries, infos):
        if hasattr(entry, 'rfid') and hasattr(entry, 'album_id'):
            rfid = entry.rfid
            album_id = entry.album_id
        else:
            rfid = entry.get('rfid') if isinstance(entry, dict) else None
            album_id = entry.get('album_id') if isinstance(entry, dict) else None

        cover_url = subsonic_service.get_cover_static_url(album_id, size=180, absolute=False) if album_id else None
        enriched.append({
            "rfid": rfid,
            "album_id": album_id,
            "album_name": (info or {}).get("name", ""),
            "artist_name": (info or {}).get("artist", ""),
            "cover_url": cover_url,
        })

    return templates.TemplateResponse(
        "albums.html",
        {"request": request, "albums": enriched, "config": config}
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
    return templates.TemplateResponse("subsonic_artists.html", {"request": request, "artists": artists, "config": config})

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
    return templates.TemplateResponse("subsonic_albums.html", {"request": request, "albums": albums, "artist_id": artist_id, "artist_name": artist_name, "config": config})

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
    return templates.TemplateResponse("subsonic_album_songs.html", {"request": request, "songs": songs, "album_id": album_id, "artist_id": artist_id, "artist_name": artist_name, "album_name": album_name, "config": config})

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


# Kiosk API: Dynamic component loading
@router.get("/kiosk/html/component", response_class=HTMLResponse)
async def get_kiosk_component(request: Request, component_name: str = Query(...)):
    """
    Returns HTML for a specific kiosk component.
    Used for dynamic content loading in kiosk mode.
    """
    component_map = {
        'player': 'components/kiosk/_player_status.html',
        'library': 'components/kiosk/_media_library.html',
        'playlist': 'components/kiosk/_playlist_view.html',
        'devices': 'components/kiosk/_device_selector.html',
        'system': 'components/kiosk/_system_menu.html',
        'nfc': 'components/kiosk/_nfc_encoding.html',
    }

    template_path = component_map.get(component_name)
    print(f"[DEBUG] get_kiosk_component called with: {component_name}, template_path: {template_path}")
    
    if not template_path:
        raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")

    try:
        return templates.TemplateResponse(template_path, {"request": request, "config": config})
    except Exception as e:
        print(f"[DEBUG] Error loading template {template_path}: {e}")
        raise HTTPException(status_code=404, detail=f"Failed to load template: {str(e)}")

@router.get("/kiosk/html/media_library/albums", response_class=HTMLResponse)
async def kiosk_artist_albums(request: Request, artist_id: str = Query(...), artist_name: str = Query(...)):
    """
    Render all album cards for a given artist as HTML using the album partial.
    """
    subsonic_service = get_service("subsonic_service")
    albums = subsonic_service.list_albums_for_artist(artist_id)
    if not albums:
        raise HTTPException(status_code=404, detail="No albums found for artist")
    artist = {"name": artist_name}
    return templates.TemplateResponse(
        "components/kiosk/media_library/_albums_container.html",
        {"request": request, "albums": albums, "artist": artist}
    )


@router.get("/kiosk/html/devices", response_class=HTMLResponse)
async def kiosk_devices(request: Request):
    """
    Render available output devices (Bluetooth/MPV + Chromecast) as HTML.
    """
    async with httpx.AsyncClient() as client:
        status_resp = await client.get(
            f"{LOCAL_API_BASE}/api/output/status",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()

        options_resp = await client.get(
            f"{LOCAL_API_BASE}/api/output/options",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        options_resp.raise_for_status()
        options_data = options_resp.json()

    active_backend = status_data.get("active_backend")
    active_device = status_data.get("active_device")
    readiness = status_data.get("output_readiness") or {}

    bt_label = "Bluetooth Speaker"
    if not config.BT_SPEAKER_MAC:
        bt_label = "Local MPV Output"

    devices = [
        {
            "name": bt_label,
            "backend": "mpv",
            "switch_device_name": None,
            "icon": "mdi-bluetooth-audio",
            "subtitle": "Local output",
            "is_active": active_backend == "mpv",
            "is_ready": readiness.get("ready", True),
        }
    ]

    for device_name in options_data.get("chromecast_devices", []):
        devices.append(
            {
                "name": device_name,
                "backend": "chromecast",
                "switch_device_name": device_name,
                "icon": "mdi-cast",
                "subtitle": "Chromecast",
                "is_active": active_backend == "chromecast" and device_name == active_device,
                "is_ready": True,
            }
        )

    return templates.TemplateResponse(
        "components/kiosk/device_selector/_devices_container.html",
        {"request": request, "devices": devices}
    )


@router.get("/kiosk/html/media_library/artists", response_class=HTMLResponse)
async def kiosk_group_artists(request: Request, group_name: str = Query(...)):
    """
    Render all artist cards for a given group as HTML using the artist partial.
    """
    subsonic_service = get_service("subsonic_service")
    all_artists = subsonic_service.list_artists()
    if not all_artists:
        raise HTTPException(status_code=404, detail="No artists found")

    # Group ranges mirror the client-side grouping logic
    group_ranges = {
        'A-D': ['A', 'E'],
        'E-H': ['E', 'I'],
        'I-L': ['I', 'M'],
        'M-P': ['M', 'Q'],
        'Q-T': ['Q', 'U'],
        'U-Z': ['U', '[']
    }
    group_range = group_ranges.get(group_name)
    if not group_range:
        raise HTTPException(status_code=400, detail="Invalid group name")

    # Filter artists safely (support dict or object shapes)
    filtered_artists = []
    for a in all_artists:
        name = a.get('name') if isinstance(a, dict) else getattr(a, 'name', '')
        if not name:
            continue
        first = name.upper()[0]
        if first >= group_range[0] and first < group_range[1]:
            filtered_artists.append(a)

    if not filtered_artists:
        return HTMLResponse('<div class="text-center text-muted py-5">No artists found</div>')

    return templates.TemplateResponse(
        "components/kiosk/media_library/_artists_container.html",
        {"request": request, "artists": filtered_artists}
    )


@router.get("/kiosk/html/playlist", response_class=HTMLResponse)
async def kiosk_playlist(request: Request):
    """
    Render the current playlist as an HTML fragment for kiosk.
    Calls the internal API `/api/mediaplayer/current_track` which returns
    the playlist and current_track information.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LOCAL_API_BASE}/api/mediaplayer/current_track",
            headers=FORWARDED_HEADERS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()

    playlist = data.get("playlist", [])
    current = data.get("current_track")

    return templates.TemplateResponse(
        "components/kiosk/playlist/_playlist_container.html",
        {"request": request, "playlist": playlist, "current_track": current}
    )

