
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import FileResponse
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List
from app.database.album_schema import AlbumEntry
from app.database.album_db import AlbumDatabase
from app.services.subsonic_service import SubsonicService
from app.config import config
from app.config import config
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/albums", response_model=List[AlbumEntry])
def list_album_entries_route():
    album_db = AlbumDatabase(config)
    subsonic = SubsonicService(config)
    mappings = album_db.list_all()
    result = []
    for rfid, album_id in mappings:
        if album_id is not None:
#            album_info = subsonic.get_album_info(album_id)
#            tracks = subsonic.get_album_tracks(album_id)
            result.append(AlbumEntry(
                rfid=rfid,
                album_id=album_id,
            ))
    return result

@router.get("/api/albums/{rfid}", response_model=AlbumEntry)
def get_album_entry(rfid: str):
    album_db = AlbumDatabase(config)
    subsonic = SubsonicService(config)
    album_id = album_db.get_album_id_by_rfid(rfid)
    if not album_id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return AlbumEntry(
        rfid=rfid,
        album_id=album_id,
    )

@router.post("/api/albums/{rfid}")
def create_album_entry_route(rfid: str, album_id: str = Body(...)):
    album_db = AlbumDatabase(config)
    album_db.set_album_mapping(rfid, album_id)
    return {"status": "created", "rfid": rfid, "album_id": album_id}

# Update RFID for a given album_id
@router.put("/api/albums/update/{rfid}/from/{album_id}", response_model=AlbumEntry)
def update_rfid_from_album_id(rfid: str, album_id: str):
    album_db = AlbumDatabase(config)
    album_db.update_rfid_from_album_id(rfid, album_id)
    return AlbumEntry(rfid=rfid, album_id=album_id)

# Update album_id for a given rfid 
@router.put("/api/albums/update/{album_id}/from/{rfid}", response_model=AlbumEntry)
def update_album_id_from_rfid(album_id: str, rfid: str):
    album_db = AlbumDatabase(config)
    album_db.update_album_id_from_rfid(rfid, album_id)
    return AlbumEntry(rfid=rfid, album_id=album_id)


@router.put("/api/albums/{rfid}/{album_id}", response_model=AlbumEntry)
def update_album_entry_route(rfid: str, album_id: str):
    album_db = AlbumDatabase(config)
    album_db.set_album_mapping(rfid, album_id)
    return AlbumEntry(
        rfid=rfid,
        album_id=album_id,
    )

@router.delete("/api/albums/{rfid}")
def delete_album_entry_route(rfid: str):
    album_db = AlbumDatabase(config)
    album_db.delete_mapping(rfid)
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
    response = requests.get(cover_url, timeout=config.HTTP_REQUEST_TIMEOUT)
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