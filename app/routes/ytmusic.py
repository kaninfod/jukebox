
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.schemas.ytmusic import YTMusicEntry, YTMusicEntryUpdate
from app.models.ytmusic import YTMusicModel, Base
from ytmusicapi import YTMusic, OAuthCredentials
import json

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://dbuser:4AllData@192.168.68.102:3306/hingedb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()
ytmusic = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id="194320065459-2854gle26f6899bg7mt1e579q0rvmnr1.apps.googleusercontent.com", client_secret="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"))

def get_db():
    # Create table if it doesn't exist (only when database is accessed)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_ytmusic_entry(rfid: str):
    """Helper function to create RFID entry - can be called from outside FastAPI context"""
    try:
        db = SessionLocal()
        try:
            # Create table if it doesn't exist
            Base.metadata.create_all(bind=engine)
            
            # Check if RFID already exists
            existing_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
            if existing_entry:
                print(f"RFID {rfid} already exists in database")
                return {"status": "RFID already exists", "rfid": rfid}
            
            # Create new entry with only RFID
            db_entry = YTMusicModel(
                rfid=rfid,
                album_name=None,
                artist_name=None,
                year=None,
                yt_id=None,
                thumbnail=None,
                tracks=None
            )
            db.add(db_entry)
            db.commit()
            print(f"Created new RFID entry: {rfid}")
            return {"status": "RFID created", "rfid": rfid}
        finally:
            db.close()
    except Exception as e:
        print(f"Database unavailable - RFID {rfid} not saved to database: {e}")
        return {"status": "Database unavailable", "rfid": rfid, "message": "RFID detected but not saved"}

@router.get("/ytmusic", response_model=List[YTMusicEntry])
def list_ytmusic(db: Session = Depends(get_db)):
    return db.query(YTMusicModel).all()

@router.get("/ytmusic/{rfid}", response_model=YTMusicEntry)
def get_ytmusic(rfid: str, db: Session = Depends(get_db)):
    entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/ytmusic/{rfid}")
def create_ytmusic(rfid: str, db: Session = Depends(get_db)):
    # Check if RFID already exists
    existing_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if existing_entry:
        return {"status": "RFID already exists", "rfid": rfid}
    
    # Create new entry with only RFID
    db_entry = YTMusicModel(
        rfid=rfid,
        album_name=None,
        artist_name=None,
        year=None,
        yt_id=None,
        thumbnail=None,
        tracks=None
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return {"status": "RFID created", "rfid": rfid}

@router.put("/ytmusic/{rfid}/{audioPlaylistId}", response_model=YTMusicEntry)
def update_ytmusic(rfid: str, audioPlaylistId: str, db: Session = Depends(get_db)):
    # Check if RFID exists
    db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    try:
        # Get album info from YouTube Music
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        
        # Extract album information
        album_name = album_info.get('title', 'Unknown Album')
        artist_name = 'Unknown Artist'
        if album_info.get('artists') and len(album_info['artists']) > 0:
            artist_name = album_info['artists'][0].get('name', 'Unknown Artist')
        year = album_info.get('year', None)
        
        # Extract thumbnail (120x120 size)
        thumbnail = None
        thumbnails = album_info.get('thumbnails', [])
        for thumb in thumbnails:
            if thumb.get('width') == 120 and thumb.get('height') == 120:
                thumbnail = thumb.get('url')
                break
        
        # Extract tracks information
        tracks_data = []
        tracks = album_info.get('tracks', [])
        for track in tracks:
            track_info = {
                'title': track.get('title', 'Unknown Title'),
                'duration': track.get('duration', '0:00'),
                'track_number': track.get('trackNumber', 0),
                'video_id': track.get('videoId', '')
            }
            tracks_data.append(track_info)
        
        # Update database entry
        db_entry.album_name = album_name
        db_entry.artist_name = artist_name
        db_entry.year = year
        db_entry.yt_id = audioPlaylistId
        db_entry.thumbnail = thumbnail
        db_entry.tracks = json.dumps(tracks_data)  # Store as JSON string
        
        db.commit()
        db.refresh(db_entry)
        return db_entry
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get album info: {str(e)}")

@router.delete("/ytmusic/{rfid}")
def delete_ytmusic(rfid: str, db: Session = Depends(get_db)):
    db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(db_entry)
    db.commit()
    return {"status": "deleted"}


@router.get("/ytmusic/album_browse_id/{audioPlaylistId}")
def get_album(audioPlaylistId: str):
    try:
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        return album_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))