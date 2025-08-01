from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://dbuser:4AllData@192.168.68.102:3306/hingedb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class YTMusicModel(Base):
    __tablename__ = "ytmusic"
    rfid = Column(String(64), primary_key=True, index=True)
    album_name = Column(String(255))
    artist_name = Column(String(255))
    year = Column(Integer)
    yt_id = Column(String(64))

# Create table if it doesn't exist
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class YTMusicEntry(BaseModel):
    rfid: str
    album_name: str
    artist_name: str
    year: int
    yt_id: str
    class Config:
        orm_mode = True

class YTMusicEntryUpdate(BaseModel):
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    yt_id: Optional[str] = None

router = APIRouter()

def get_db():
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
