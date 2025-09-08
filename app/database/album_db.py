import logging
from sqlalchemy.orm import Session
from app.database.album import AlbumModel, Base
from app.config import config
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Database setup
SQLALCHEMY_DATABASE_URL = config.get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_album_entry(rfid: str):
    """Create a new AlbumModel entry with only RFID."""
    logger.info(f"Attempting to create Album entry for RFID: {rfid}")
    try:
        db = SessionLocal()
        try:
            Base.metadata.create_all(bind=engine)
            existing_entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if existing_entry:
                logger.info(f"RFID already exists: {rfid}")
                return {"status": "RFID already exists", "rfid": rfid}
            db_entry = AlbumModel(
                rfid=rfid,
                provider="youtube_music",
                album_name=None,
                artist_name=None,
                year=None,
                audioPlaylistId=None,
                thumbnail=None,
                tracks=None
            )
            db.add(db_entry)
            db.commit()
            logger.info(f"RFID created: {rfid}")
            return {"status": "RFID created", "rfid": rfid}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database unavailable, RFID {rfid} not saved: {e}")
        return {"status": "Database unavailable", "rfid": rfid, "message": f"RFID detected but not saved: {e}"}

def list_album_entries():
    logger.info("Listing all album entries from database")
    db = SessionLocal()
    try:
        entries = db.query(AlbumModel).all()
        logger.info(f"Found {len(entries)} album entries")
        return entries
    except Exception as e:
        logger.error(f"Error listing album entries: {e}")
        return []
    finally:
        db.close()

def get_album_entry_by_rfid(rfid: str):
    logger.info(f"Retrieving Album entry for RFID: {rfid}")
    db = SessionLocal()
    try:
        entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
        if entry:
            logger.info(f"Found Album entry for RFID: {rfid}")
        else:
            logger.warning(f"No Album entry found for RFID: {rfid}")
        return entry
    except Exception as e:
        logger.error(f"Error retrieving Album entry for RFID {rfid}: {e}")
        return None
    finally:
        db.close()

def update_album_entry(rfid: str, album_data: dict):
    logger.info(f"Updating Album entry for RFID: {rfid} with data: {album_data}")
    db = SessionLocal()
    try:
        db_entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
        if not db_entry:
            logger.warning(f"No Album entry found for update, RFID: {rfid}")
            return None
        for key, value in album_data.items():
            if hasattr(db_entry, key):
                setattr(db_entry, key, value)
        db.commit()
        db.refresh(db_entry)
        logger.info(f"Updated Album entry for RFID: {rfid}")
        return db_entry
    except Exception as e:
        logger.error(f"Error updating Album entry for RFID {rfid}: {e}")
        return None
    finally:
        db.close()

def delete_album_entry(rfid: str):
    logger.info(f"Deleting Album entry for RFID: {rfid}")
    db = SessionLocal()
    try:
        db_entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
        if not db_entry:
            logger.warning(f"No Album entry found to delete, RFID: {rfid}")
            return False
        db.delete(db_entry)
        db.commit()
        logger.info(f"Deleted Album entry for RFID: {rfid}")
        return True
    except Exception as e:
        logger.error(f"Error deleting Album entry for RFID {rfid}: {e}")
        return False
    finally:
        db.close()

def get_album_data_by_audioPlaylistId(audioPlaylistId: str):
    """Get Album data from database by audioPlaylistId"""
    if not audioPlaylistId:
        logger.warning("No audioPlaylistId provided to get_album_data_by_audioPlaylistId")
        return None
    try:
        db = SessionLocal()
        try:
            # Query by audioPlaylistId instead of rfid
            entry = db.query(AlbumModel).filter(AlbumModel.audioPlaylistId == audioPlaylistId).first()
            if entry:
                # Parse track data if available
                tracks_data = []
                if entry.tracks:
                    try:
                        tracks_data = json.loads(entry.tracks)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse tracks JSON data")
                # Get first track title if available
                track_title = "No Track"
                if tracks_data and len(tracks_data) > 0:
                    track_title = tracks_data[0].get('title', 'No Track')
                logger.info(f"Found Album data for audioPlaylistId: {audioPlaylistId}")
                return {
                    "album_name": entry.album_name,
                    "artist_name": entry.artist_name,
                    "year": entry.year,
                    "thumbnail": entry.thumbnail,
                    "audioPlaylistId": entry.audioPlaylistId,
                    "first_track": track_title,
                    "tracks": tracks_data
                }
            else:
                logger.warning(f"No Album entry found for audioPlaylistId: {audioPlaylistId}")
                return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get Album data for audioPlaylistId {audioPlaylistId}: {e}")
        return None

# def load_album_data_to_screen(rfid: str, screen_manager):
#     """Load Album data from database and update the home screen"""
#     logger.info(f"Loading Album data for RFID: {rfid} to screen")
#     try:
#         db = SessionLocal()
#         try:
#             # Get the entry from database
#             entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
#             if not entry:
#                 logger.warning(f"No Album entry found for RFID: {rfid}")
#                 return
#             # Get the home screen
#             home_screen = screen_manager.screens.get('home')
#             if not home_screen:
#                 logger.error("Home screen not available")
#                 return
#             # Parse track data if available
#             tracks_data = []
#             if entry.tracks:
#                 try:
#                     tracks_data = json.loads(entry.tracks)
#                 except json.JSONDecodeError:
#                     logger.error("Failed to parse tracks JSON data")
#             # Get first track title if available
#             track_title = "No Track"
#             if tracks_data and len(tracks_data) > 0:
#                 track_title = tracks_data[0].get('title', 'No Track')
#             artist_name = entry.artist_name or "Unknown Artist"
#             album_name = entry.album_name or "Unknown Album"
#             year = entry.year or "----"
#             audioPlaylistId = entry.audioPlaylistId or ""
#             # Get current volume from screen
#             current_volume = home_screen.volume
#             # Switch to home screen and render
#             screen_manager.switch_to_screen("home")
#             logger.info(f"Loaded album: {entry.album_name} by {entry.artist_name}")
#         finally:
#             db.close()
#     except Exception as e:
#         logger.error(f"Failed to load Album data for RFID {rfid}: {e}")
#         # Fallback - just show the RFID
#         home_screen = screen_manager.screens.get('home')
#         if home_screen:
#             home_screen.set_track_info(
#                 artist="Unknown",
#                 album=f"RFID: {rfid}",
#                 year="",
#                 track="No Data Available",
#                 image_url=None,
#                 audioPlaylistId=""
#             )
#             home_screen.set_player_status("standby")
#             screen_manager.switch_to_screen("home")
