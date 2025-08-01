from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class YTMusicModel(Base):
    __tablename__ = "ytmusic"
    rfid = Column(String(64), primary_key=True, index=True)
    album_name = Column(String(255))
    artist_name = Column(String(255))
    year = Column(Integer)
    yt_id = Column(String(64))
