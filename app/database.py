"""
Database operations for the jukebox.
Handles YTMusic data loading and database interactions.
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1OGUxMjRkNjNkODU0ZGRmODVmNmY4YjVmYWNiMWRjMCIsImlhdCI6MTc1NDA2Nzk0MCwiZXhwIjoyMDY5NDI3OTQwfQ.UMME9LQrS2NzEkscVi-ZTneCJ_pJ3DXK6sD-3BEo7g4
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ytmusic import YTMusicModel
from app.devices.mqtt import (
    publish_artist, publish_album, publish_year, 
    publish_track, publish_status, publish_yt_id
)
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
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://dbuser:4AllData@192.168.68.102:3306/hingedb"
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
            home_screen.set_track_info(
                artist=entry.artist_name or "Unknown Artist",
                album=entry.album_name or "Unknown Album", 
                year=entry.year,
                track=track_title,
                image_url=entry.thumbnail,
                yt_id=entry.yt_id
            )
            
            # Set player status to play (since we just loaded an album)
            home_screen.set_player_status("play")
            
            # Publish all information to MQTT
            artist_name = entry.artist_name or "Unknown Artist"
            album_name = entry.album_name or "Unknown Album"
            year = entry.year or "----"
            yt_id = entry.yt_id or ""
            
            publish_artist(artist_name)
            publish_album(album_name)
            publish_year(year)
            publish_track(track_title)
            publish_status("playing")
            publish_yt_id(yt_id)
            
            # Get current volume from screen
            current_volume = home_screen.volume
            
            # publish_full_info is called automatically by each publish function
            
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
            
            # Publish fallback info to MQTT
            publish_artist("Unknown")
            publish_album(f"RFID: {rfid}")
            publish_year("----")
            publish_track("No Data Available")
            publish_status("idle")
            publish_yt_id("")
            # publish_full_info is called automatically by each publish function
            
            screen_manager.switch_to_screen("home")
