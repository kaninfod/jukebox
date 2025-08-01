
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.schemas.ytmusic import YTMusicEntry, YTMusicEntryUpdate
from app.models.ytmusic import YTMusicModel, Base
from ytmusicapi import YTMusic, OAuthCredentials

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

@router.get("/ytmusic", response_model=List[YTMusicEntry])
def list_ytmusic(db: Session = Depends(get_db)):
    return db.query(YTMusicModel).all()

@router.get("/ytmusic/{rfid}", response_model=YTMusicEntry)
def get_ytmusic(rfid: str, db: Session = Depends(get_db)):
    entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/ytmusic", response_model=YTMusicEntry)
def create_ytmusic(entry: YTMusicEntry, db: Session = Depends(get_db)):
    if db.query(YTMusicModel).filter(YTMusicModel.rfid == entry.rfid).first():
        raise HTTPException(status_code=400, detail="RFID already exists")
    db_entry = YTMusicModel(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/ytmusic/{rfid}", response_model=YTMusicEntry)
def update_ytmusic(rfid: str, entry: YTMusicEntryUpdate, db: Session = Depends(get_db)):
    db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in entry.dict(exclude_unset=True).items():
        setattr(db_entry, field, value)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/ytmusic/{rfid}")
def delete_ytmusic(rfid: str, db: Session = Depends(get_db)):
    db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(db_entry)
    db.commit()
    return {"status": "deleted"}


@router.get("/ytmusic/album_browse_id/{audioPlaylistId}")
def get_album_browse_id(audioPlaylistId: str):
    try:
        browse_id = ytmusic.get_album_browse_id(audioPlaylistId)
        album_info = ytmusic.get_album(browse_id)
        return album_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))