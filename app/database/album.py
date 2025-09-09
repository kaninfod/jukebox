from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AlbumModel(Base):
    __tablename__ = "albums"
    rfid = Column(String(64), primary_key=True, index=True)
    provider = Column(String(32), default="subsonic")
    album_name = Column(String(255))
    artist_name = Column(String(255))
    year = Column(Integer)
    audioPlaylistId = Column(String(64))
    thumbnail = Column(String(500))  
    tracks = Column(Text)
