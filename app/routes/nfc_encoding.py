
from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.service_container import get_service
from app.services.nfc_encoding_session import nfc_encoding_session

router = APIRouter()


@router.post("/api/nfc-encoding/start")
async def start_nfc_encoding(request: Request):
    data = await request.json()
    album_id = data.get("album_id")
    if not album_id:
        raise HTTPException(status_code=400, detail="album_id is required")
    app_state = get_service("app_state")
    if app_state.is_encoding_mode_active():
        raise HTTPException(status_code=409, detail="NFC encoding session already active")
    nfc_encoding_session.start(album_id)
    app_state.enable_encoding_mode()
    return {"status": "encoding_mode_enabled", "album_id": album_id}

@router.post("/api/nfc-encoding/stop")
def stop_nfc_encoding():
    app_state = get_service("app_state")
    if not app_state.is_encoding_mode_active():
        raise HTTPException(status_code=409, detail="NFC encoding session not active")
    app_state.disable_encoding_mode()
    return {"status": "encoding_mode_disabled"}


@router.get("/api/nfc-encoding/status")
def nfc_encoding_status():
    app_state = get_service("app_state")
    return {
        "encoding_mode": app_state.is_encoding_mode_active(),
        "state": app_state.get_app_state().name,
        "success": nfc_encoding_session.success,
        "last_uid": nfc_encoding_session.last_uid,
        "album_id": nfc_encoding_session.album_id
    }
