from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import FileResponse
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List
from app.schemas.ytmusic import YTMusicEntry, YTMusicEntryUpdate
from app.database import (
    create_ytmusic_entry,
    list_album_entries,
    get_ytmusic_entry_by_rfid,
    update_ytmusic_entry,
    delete_ytmusic_entry
)
from ytmusicapi import YTMusic, OAuthCredentials
from app.config import config
import json
import logging

logger = logging.getLogger(__name__)


router = APIRouter()

client_id = config.YTMUSIC_CLIENT_ID
client_secret = config.YTMUSIC_CLIENT_SECRET
oauth_file = 'oauth.json'
ytmusic = YTMusic(oauth_file, oauth_credentials=OAuthCredentials(client_id=client_id, client_secret=client_secret))


# --- Place the /ytmusic/album_card endpoint first to avoid collision ---
from pydantic import BaseModel

class AlbumCardRequest(BaseModel):
    audioPlaylistId: str
    output_filename: str = None
    album_title: str = None


@router.post("/ytmusic/album_card")
def api_create_album_card(payload: AlbumCardRequest):
    from app.services.ytmusic_service import YTMusicService
    try:
        service = YTMusicService()
        album_info = service.get_album_info(payload.audioPlaylistId)
        yt_album_title = album_info.get('title', 'Unknown Album')
        album_title_final = payload.album_title if payload.album_title else yt_album_title
        artist = 'Unknown Artist'
        if album_info.get('artists') and len(album_info['artists']) > 0:
            artist = album_info['artists'][0].get('name', 'Unknown Artist')
        # Find a thumbnail close to 540px wide
        cover_url = None
        thumbnails = album_info.get('thumbnails', [])
        best_size = 0
        for thumb in thumbnails:
            w = thumb.get('width', 0)
            if w >= 500 and (best_size == 0 or abs(w-540) < abs(best_size-540)):
                cover_url = thumb.get('url')
                best_size = w
        if not cover_url and thumbnails:
            cover_url = thumbnails[-1].get('url')
        if not cover_url:
            raise HTTPException(status_code=404, detail="No suitable album cover found.")
        # Output path
        output_dir = getattr(config, "ALBUM_COVER_CACHE_PATH", "album_covers")
        os.makedirs(output_dir, exist_ok=True)
        if payload.output_filename:
            output_path = os.path.join(output_dir, payload.output_filename)
        else:
            output_path = os.path.join(output_dir, f"album_card_{payload.audioPlaylistId}.png")
        result_path = create_album_card(
            cover_url=cover_url,
            album_title=album_title_final,
            artist=artist,
            output_path=output_path
        )
        return FileResponse(result_path, media_type="image/png", filename=os.path.basename(result_path))
    except Exception as e:
        logger.error(f"Failed to create album card: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create album card: {str(e)}")

@router.get("/ytmusic", response_model=List[YTMusicEntry])
def list_ytmusic_entries():
    entries = list_album_entries()
    # Convert ORM objects to Pydantic models
    return [YTMusicEntry.from_orm(e) for e in entries]

@router.get("/ytmusic/{rfid}", response_model=YTMusicEntry)
def get_ytmusic(rfid: str):
    entry = get_ytmusic_entry_by_rfid(rfid)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/ytmusic/{rfid}")
def create_ytmusic(rfid: str):
    return create_ytmusic_entry(rfid)

from app.services.ytmusic_service import YTMusicService

@router.put("/ytmusic/{rfid}/{audioPlaylistId}", response_model=YTMusicEntry)
def update_ytmusic(rfid: str, audioPlaylistId: str):
    try:
        service = YTMusicService()
        db_entry = service.add_or_update_album_entry(rfid, audioPlaylistId)
        if not db_entry:
            raise HTTPException(status_code=404, detail="Entry not found or failed to update")
        return db_entry
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get album info: {str(e)}")

@router.delete("/ytmusic/{rfid}")
def delete_ytmusic(rfid: str):
    deleted = delete_ytmusic_entry(rfid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted"}





# Utility function to create an album card image from a URL and album info
def create_album_card(
    cover_url,
    album_title,
    artist,
    output_path,
    card_size=(540, 860),
    font_size=40,
    bottom_height_ratio=0.28,
    blend_transition_px=5
):
    import requests
    from io import BytesIO
    # Download cover image from URL
    response = requests.get(cover_url, timeout=10)
    response.raise_for_status()
    cover = Image.open(BytesIO(response.content)).convert("RGB")
    card = Image.new("RGB", card_size, (255, 255, 255))
    card_width, card_height = card_size
    bottom_height = int(card_height * bottom_height_ratio)
    cover_height = card_height - bottom_height
    cover_resized = cover.resize((card_width, cover_height))
    card.paste(cover_resized, (0, 0))
    blend_px = min(blend_transition_px, bottom_height)
    if blend_px > 0:
        tile_strip = cover_resized.crop((0, cover_height - blend_px, card_width, cover_height))
        tiled = Image.new("RGB", (card_width, bottom_height))
        for y in range(0, bottom_height, blend_px):
            box = (0, y)
            tiled.paste(tile_strip, box)
        blurred_strip = tiled.filter(ImageFilter.GaussianBlur(radius=20))
        card.paste(blurred_strip, (0, cover_height))
    else:
        strip_box = (0, cover_height - bottom_height, card_width, cover_height)
        cover_strip = cover_resized.crop(strip_box)
        blurred_strip = cover_strip.filter(ImageFilter.GaussianBlur(radius=20))
        card.paste(blurred_strip, (0, cover_height))
    blend_px = min(blend_transition_px, bottom_height)
    if blend_px > 0:
        cover_blend = cover_resized.crop((0, cover_height - blend_px, card_width, cover_height)).convert('RGBA')
        gradient = Image.new('L', (card_width, blend_px), color=0)
        for y in range(blend_px):
            alpha = int(255 * (1 - y / (blend_px - 1)))
            for x in range(card_width):
                gradient.putpixel((x, y), alpha)
        cover_blend.putalpha(gradient)
        card.paste(cover_blend.convert('RGB'), (0, cover_height), cover_blend)
    draw = ImageDraw.Draw(card)
    # Load OpenSans-Semibold.ttf from config FONT_DEFINITIONS
    from app.config import config
    font_path = None
    # Prefer Semibold font
    for font_def in config.FONT_DEFINITIONS:
        if "oswald_semi_bold" in font_def.get("name", ""):
            font_path = font_def["path"]
            break
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception as e:
        font = ImageFont.load_default()
    text = f"{album_title}\n{artist}"
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (card_width - text_w) // 2
    text_y = cover_height + (bottom_height - text_h) // 2
    shadow_offset = 2
    shadow_color = (30, 30, 30)
    draw.multiline_text((text_x+shadow_offset, text_y+shadow_offset), text, font=font, fill=shadow_color, align="center")
    draw.multiline_text((text_x, text_y), text, font=font, fill="white", align="center")
    card.save(output_path)
    return output_path