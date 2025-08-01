from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import mariadb
from ytmusicapi import YTMusic, OAuthCredentials

router = APIRouter()
ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id="194320065459-2854gle26f6899bg7mt1e579q0rvmnr1.apps.googleusercontent.com", client_secret="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"))

# Database connection config
DB_CONFIG = {
    "host": "192.168.68.102",
    "port": 3306,
    "user": "dbuser",
    "password": "4AllData",
    "database": "hingedb"
}

def get_db():
    return mariadb.connect(**DB_CONFIG)

class YTMusicEntry(BaseModel):
    rfid: str
    album_name: str
    artist_name: str
    year: int
    yt_id: str

class YTMusicEntryUpdate(BaseModel):
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    yt_id: Optional[str] = None

# Ensure table exists
with get_db() as conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ytmusic (
            rfid VARCHAR(64) PRIMARY KEY,
            album_name VARCHAR(255),
            artist_name VARCHAR(255),
            year INT,
            yt_id VARCHAR(64)
        )
    """)
    conn.commit()

@router.get("/ytmusic", response_model=List[YTMusicEntry])
def list_ytmusic():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT rfid, album_name, artist_name, year, yt_id FROM ytmusic")
        rows = cur.fetchall()
        return [YTMusicEntry(rfid=row[0], album_name=row[1], artist_name=row[2], year=row[3], yt_id=row[4]) for row in rows]

@router.get("/ytmusic/{rfid}", response_model=YTMusicEntry)
def get_ytmusic(rfid: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT rfid, album_name, artist_name, year, yt_id FROM ytmusic WHERE rfid=?", (rfid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        return YTMusicEntry(rfid=row[0], album_name=row[1], artist_name=row[2], year=row[3], yt_id=row[4])

@router.post("/ytmusic", response_model=YTMusicEntry)
def create_ytmusic(entry: YTMusicEntry):
    with get_db() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO ytmusic (rfid, album_name, artist_name, year, yt_id) VALUES (?, ?, ?, ?, ?)",
                        (entry.rfid, entry.album_name, entry.artist_name, entry.year, entry.yt_id))
            conn.commit()
        except mariadb.IntegrityError:
            raise HTTPException(status_code=400, detail="RFID already exists")
        return entry

@router.put("/ytmusic/{rfid}", response_model=YTMusicEntry)
def update_ytmusic(rfid: str, entry: YTMusicEntryUpdate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT rfid FROM ytmusic WHERE rfid=?", (rfid,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Entry not found")
        update_fields = []
        values = []
        if entry.album_name is not None:
            update_fields.append("album_name=?")
            values.append(entry.album_name)
        if entry.artist_name is not None:
            update_fields.append("artist_name=?")
            values.append(entry.artist_name)
        if entry.year is not None:
            update_fields.append("year=?")
            values.append(entry.year)
        if entry.yt_id is not None:
            update_fields.append("yt_id=?")
            values.append(entry.yt_id)
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        values.append(rfid)
        cur.execute(f"UPDATE ytmusic SET {', '.join(update_fields)} WHERE rfid=?", tuple(values))
        conn.commit()
        # Return updated entry
        cur.execute("SELECT rfid, album_name, artist_name, year, yt_id FROM ytmusic WHERE rfid=?", (rfid,))
        row = cur.fetchone()
        return YTMusicEntry(rfid=row[0], album_name=row[1], artist_name=row[2], year=row[3], yt_id=row[4])

@router.delete("/ytmusic/{rfid}")
def delete_ytmusic(rfid: str):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM ytmusic WHERE rfid=?", (rfid,))
        conn.commit()
        return {"status": "deleted"}



@router.get("/ytmusic/album_browse_id/{audioPlaylistId}")
def get_album_browse_id(audioPlaylistId: str):
    try:
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        return album_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))