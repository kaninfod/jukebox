from sqlalchemy.orm import Session
from app.models.ytmusic import YTMusicModel, Base
from app.config import config
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
SQLALCHEMY_DATABASE_URL = config.get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_ytmusic_entry(rfid: str):
    """Create a new YTMusicModel entry with only RFID."""
    try:
        db = SessionLocal()
        try:
            Base.metadata.create_all(bind=engine)
            existing_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
            if existing_entry:
                return {"status": "RFID already exists", "rfid": rfid}
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
            return {"status": "RFID created", "rfid": rfid}
        finally:
            db.close()
    except Exception as e:
        return {"status": "Database unavailable", "rfid": rfid, "message": f"RFID detected but not saved: {e}"}

def list_ytmusic_entries():
    db = SessionLocal()
    try:
        return db.query(YTMusicModel).all()
    finally:
        db.close()

def get_ytmusic_entry_by_rfid(rfid: str):
    db = SessionLocal()
    try:
        return db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
    finally:
        db.close()

def update_ytmusic_entry(rfid: str, album_data: dict):
    db = SessionLocal()
    try:
        db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
        if not db_entry:
            return None
        for key, value in album_data.items():
            setattr(db_entry, key, value)
        db.commit()
        db.refresh(db_entry)
        return db_entry
    finally:
        db.close()

def delete_ytmusic_entry(rfid: str):
    db = SessionLocal()
    try:
        db_entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
        if not db_entry:
            return False
        db.delete(db_entry)
        db.commit()
        return True
    finally:
        db.close()
def get_ytmusic_entry_by_rfid(rfid: str):
    """Get YTMusicModel entry from database by RFID"""
    try:
        db = SessionLocal()
        try:
            return db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
        finally:
            db.close()
    except Exception as e:
        print(f"Failed to get YTMusic entry for RFID {rfid}: {e}")
        return None
"""
Database operations for the jukebox.
Handles YTMusic data loading and database interactions.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ytmusic import YTMusicModel
from app.config import config
import json


def get_ytmusic_data_by_yt_id(yt_id: str):
    """Get YTMusic data from database by yt_id"""
    if not yt_id:
        return None
        
    try:
        db = SessionLocal()
        try:
            # Query by yt_id instead of rfid
            entry = db.query(YTMusicModel).filter(YTMusicModel.yt_id == yt_id).first()
            
            if entry:
                # Parse track data if available
                tracks_data = []
                if entry.tracks:
                    try:
                        tracks_data = json.loads(entry.tracks)
                    except json.JSONDecodeError:
                        print("Failed to parse tracks JSON data")
                
                # Get first track title if available
                track_title = "No Track"
                if tracks_data and len(tracks_data) > 0:
                    track_title = tracks_data[0].get('title', 'No Track')
                
                return {
                    "album_name": entry.album_name,
                    "artist_name": entry.artist_name,
                    "year": entry.year,
                    "thumbnail": entry.thumbnail,
                    "yt_id": entry.yt_id,
                    "first_track": track_title,
                    "tracks": tracks_data
                }
            else:
                return None
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"Failed to get YTMusic data for yt_id {yt_id}: {e}")
        return None


# Database setup for loading YTMusic data
SQLALCHEMY_DATABASE_URL = config.get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def load_ytmusic_data_to_screen(rfid: str, screen_manager):
    """Load YTMusic data from database and update the home screen"""
    try:
        db = SessionLocal()
        try:
            # Get the entry from database
            entry = db.query(YTMusicModel).filter(YTMusicModel.rfid == rfid).first()
            
            if not entry:
                print(f"No YTMusic entry found for RFID: {rfid}")
                return
            
            # Get the home screen
            home_screen = screen_manager.screens.get('home')
            if not home_screen:
                print("Home screen not available")
                return
            
            # Parse track data if available
            tracks_data = []
            if entry.tracks:
                try:
                    tracks_data = json.loads(entry.tracks)
                except json.JSONDecodeError:
                    print("Failed to parse tracks JSON data")
            
            # Get first track title if available
            track_title = "No Track"
            if tracks_data and len(tracks_data) > 0:
                track_title = tracks_data[0].get('title', 'No Track')
            
            # Update the home screen with album data
            # home_screen.set_track_info(
            #     artist=entry.artist_name or "Unknown Artist",
            #     album=entry.album_name or "Unknown Album", 
            #     year=entry.year,
            #     track=track_title,
            #     image_url=entry.thumbnail,
            #     yt_id=entry.yt_id
            # )
            
            # # Set player status to play (since we just loaded an album)
            # home_screen.set_player_status("play")
            
            artist_name = entry.artist_name or "Unknown Artist"
            album_name = entry.album_name or "Unknown Album"
            year = entry.year or "----"
            yt_id = entry.yt_id or ""
            
            # Get current volume from screen
            current_volume = home_screen.volume
            
            # Switch to home screen and render
            screen_manager.switch_to_screen("home")
            
            print(f"Loaded album: {entry.album_name} by {entry.artist_name}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Failed to load YTMusic data for RFID {rfid}: {e}")
        # Fallback - just show the RFID
        home_screen = screen_manager.screens.get('home')
        if home_screen:
            home_screen.set_track_info(
                artist="Unknown",
                album=f"RFID: {rfid}",
                year="",
                track="No Data Available",
                image_url=None,
                yt_id=""
            )
            home_screen.set_player_status("standby")
            
            screen_manager.switch_to_screen("home")
