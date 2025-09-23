import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.album import AlbumModel, Base

logger = logging.getLogger(__name__)

class AlbumDatabase:
    def __init__(self, config):
        self.config = config
        database_url = config.get_database_url()
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)


    def set_album_mapping(self, rfid: str, album_id: str):
        session = self.SessionLocal()
        try:
            album = session.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if album:
                album.album_id = album_id
                logger.info(f"Updated mapping: {rfid} -> {album_id}")
            else:
                album = AlbumModel(rfid=rfid, album_id=album_id)
                session.add(album)
                logger.info(f"Created mapping: {rfid} -> {album_id}")
            session.commit()
        finally:
            session.close()


    def get_album_id_by_rfid(self, rfid: str):
        session = self.SessionLocal()
        try:
            album = session.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            return album.album_id if album else None
        finally:
            session.close()

    def delete_mapping(self, rfid: str):
        session = self.SessionLocal()
        try:
            album = session.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if album:
                session.delete(album)
                session.commit()
                logger.info(f"Deleted mapping for RFID: {rfid}")
        finally:
            session.close()



    def list_all(self):
        session = self.SessionLocal()
        try:
            albums = session.query(AlbumModel).all()
            return [(album.rfid, album.album_id) for album in albums]
        finally:
            session.close()

# Export for import *
__all__ = ["AlbumDatabase"]
