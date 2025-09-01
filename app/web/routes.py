
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import config
from app.routes.albums import list_album_entries_route, update_album_entry_route

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/jukebox/albums", response_class=HTMLResponse)
async def albums(request: Request):
    # Call the Python API directly
    albums = list_album_entries_route()
    # If the result is a Response object, extract .body or .json()
    if hasattr(albums, 'body'):
        import json
        albums = json.loads(albums.body)
    return templates.TemplateResponse("albums.html", {"request": request, "albums": albums, "cover_path": "album_covers"})

@router.post("/jukebox/albums/update_audioPlaylistId")
async def update_audioPlaylistId(rfid: str = Form(...), audioPlaylistId: str = Form(...)):
    # Call the Python API directly
    update_album_entry_route(rfid, audioPlaylistId)
    return RedirectResponse("/jukebox/albums", status_code=303)
