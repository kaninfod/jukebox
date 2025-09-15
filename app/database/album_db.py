import logging
from sqlalchemy.orm import Session
from app.database.album import AlbumModel, Base
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AlbumDatabase:
    """Database service for album operations with dependency injection support"""
    
    def __init__(self, config):
        """Initialize database with injected config"""
        self.config = config
        self.database_url = config.get_database_url()
        
        # SQLite-specific configuration
        if self.database_url.startswith('sqlite'):
            # Enable foreign key support and other SQLite optimizations
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},  # Allow multiple threads
                echo=False  # Set to True for SQL debugging
            )
        else:
            self.engine = create_engine(self.database_url)
            
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
        
    def create_album_entry(self, rfid: str):
        """Create a new AlbumModel entry with only RFID."""
        logger.info(f"Attempting to create Album entry for RFID: {rfid}")
        try:
            db = self.get_session()
            try:
                Base.metadata.create_all(bind=self.engine)
                existing_entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
                if existing_entry:
                    logger.info(f"RFID already exists: {rfid}")
                    return {"status": "RFID already exists", "rfid": rfid}
                db_entry = AlbumModel(
                    rfid=rfid,
                    provider="subsonic",
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

    def get_album_entry_by_rfid(self, rfid: str):
        """Get album entry by RFID"""
        logger.info(f"Getting album entry for RFID: {rfid}")
        db = self.get_session()
        try:
            entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if entry:
                return entry
            else:
                logger.info(f"No entry found for RFID: {rfid}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving album entry for RFID {rfid}: {e}")
            return None
        finally:
            db.close()

    def get_album_data_by_audioPlaylistId(self, audioPlaylistId: str):
        """Get album data by audioPlaylistId"""
        logger.info(f"Getting album data for audioPlaylistId: {audioPlaylistId}")
        db = self.get_session()
        try:
            entry = db.query(AlbumModel).filter(AlbumModel.audioPlaylistId == audioPlaylistId).first()
            if entry:
                # Convert SQLAlchemy model to dict for compatibility
                result = {
                    'rfid': entry.rfid,
                    'provider': entry.provider,
                    'album_name': entry.album_name,
                    'artist_name': entry.artist_name,
                    'year': entry.year,
                    'audioPlaylistId': entry.audioPlaylistId,
                    'thumbnail': entry.thumbnail,
                    'tracks': entry.tracks
                }
                # Parse tracks if it's a JSON string
                if isinstance(result['tracks'], str):
                    try:
                        result['tracks'] = json.loads(result['tracks'])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse tracks JSON for audioPlaylistId: {audioPlaylistId}")
                        result['tracks'] = []
                return result
            else:
                logger.info(f"No entry found for audioPlaylistId: {audioPlaylistId}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving album data for audioPlaylistId {audioPlaylistId}: {e}")
            return None
        finally:
            db.close()

    def update_album_entry(self, rfid: str, album_data: dict):
        """Update album entry with new data"""
        logger.info(f"Updating album entry for RFID: {rfid}")
        db = self.get_session()
        try:
            entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if not entry:
                logger.error(f"No entry found for RFID: {rfid}")
                return None
                
            # Update fields from album_data
            if 'album_name' in album_data:
                entry.album_name = album_data['album_name']
            if 'artist_name' in album_data:
                entry.artist_name = album_data['artist_name']
            if 'year' in album_data:
                entry.year = album_data['year']
            if 'audioPlaylistId' in album_data:
                entry.audioPlaylistId = album_data['audioPlaylistId']
            if 'thumbnail' in album_data:
                entry.thumbnail = album_data['thumbnail']
            if 'tracks' in album_data:
                entry.tracks = json.dumps(album_data['tracks']) if isinstance(album_data['tracks'], list) else album_data['tracks']
            
            db.commit()
            
            # Return data instead of the model object to avoid DetachedInstanceError
            result = {
                'rfid': entry.rfid,
                'provider': entry.provider,
                'album_name': entry.album_name,
                'artist_name': entry.artist_name,
                'year': entry.year,
                'audioPlaylistId': entry.audioPlaylistId,
                'thumbnail': entry.thumbnail,
                'tracks': entry.tracks
            }
            
            logger.info(f"Successfully updated album entry for RFID: {rfid}")
            return result
        except Exception as e:
            logger.error(f"Error updating album entry for RFID {rfid}: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def list_album_entries(self):
        """List all album entries"""
        logger.info("Listing all album entries from database")
        db = self.get_session()
        try:
            entries = db.query(AlbumModel).all()
            return [
                {
                    'rfid': entry.rfid,
                    'provider': entry.provider,
                    'album_name': entry.album_name,
                    'artist_name': entry.artist_name,
                    'year': entry.year,
                    'audioPlaylistId': entry.audioPlaylistId,
                    'thumbnail': entry.thumbnail,
                    'tracks': json.loads(entry.tracks) if entry.tracks and isinstance(entry.tracks, str) else entry.tracks
                }
                for entry in entries
            ]
        except Exception as e:
            logger.error(f"Error listing album entries: {e}")
            return []
        finally:
            db.close()

    def delete_album_entry(self, rfid: str):
        """Delete album entry by RFID"""
        logger.info(f"Deleting album entry for RFID: {rfid}")
        db = self.get_session()
        try:
            entry = db.query(AlbumModel).filter(AlbumModel.rfid == rfid).first()
            if not entry:
                logger.error(f"No entry found for RFID: {rfid}")
                return False
                
            db.delete(entry)
            db.commit()
            logger.info(f"Successfully deleted album entry for RFID: {rfid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting album entry for RFID {rfid}: {e}")
            db.rollback()
            return False
        finally:
            db.close()


# Legacy Database setup for backward compatibility
# These will be removed once all modules use dependency injection
from app.config import config
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
                provider="subsonic",
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
