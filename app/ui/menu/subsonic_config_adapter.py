"""
Subsonic configuration adapter for creating dynamic menu structures from Subsonic API data.
"""

from typing import Dict, List, Any, Optional
from .menu_node import MenuNode
from app.services.subsonic_service import SubsonicService
import logging

logger = logging.getLogger(__name__)


class SubsonicConfigAdapter:
    """
    Adapter that creates dynamic menu nodes from Subsonic API data.
    Combines static JSON configuration with dynamic music library data.
    """
    
    def __init__(self, subsonic_service: SubsonicService):
        """
        Initialize the Subsonic config adapter.
        
        Args:
            subsonic_service: Instance of SubsonicService for data fetching
        """
        self.subsonic_service = subsonic_service
        self._cached_menu_data = {}
        logger.info("SubsonicConfigAdapter initialized")

    def create_artists_alphabetical_menu(self) -> List[MenuNode]:
        """
        Create menu nodes for alphabetical artist groups (A-D, E-H, etc.).
        
        Returns:
            List of MenuNode objects for each alphabetical group
        """
        try:
            groups = self.subsonic_service.get_alphabetical_groups()
            menu_nodes = []
            
            for group in groups:
                group_name = group["name"]
                start_letter, end_letter = group["range"]
                
                node = MenuNode(
                    id=f"artists_group_{group_name.lower().replace('-', '_')}",
                    name=group_name,
                    payload={
                        "action": "browse_artists_in_range",
                        "start_letter": start_letter,
                        "end_letter": end_letter,
                        "group_name": group_name
                    }
                )
                menu_nodes.append(node)
            
            logger.info(f"Created {len(menu_nodes)} alphabetical artist group nodes")
            return menu_nodes
            
        except Exception as e:
            logger.error(f"Failed to create artists alphabetical menu: {e}")
            return []

    def create_artists_in_range_menu(self, start_letter: str, end_letter: str) -> List[MenuNode]:
        """
        Create menu nodes for artists within a specific alphabetical range.
        
        Args:
            start_letter: Starting letter of the range
            end_letter: Ending letter of the range
            
        Returns:
            List of MenuNode objects for each artist in the range
        """
        try:
            artists = self.subsonic_service.get_artists_in_range(start_letter, end_letter)
            menu_nodes = []
            
            for artist in artists:
                artist_id = artist.get("id")
                artist_name = artist.get("name")
                
                if artist_id and artist_name:
                    node = MenuNode(
                        id=f"artist_{artist_id}",
                        name=artist_name,
                        payload={
                            "action": "browse_artist_albums",
                            "artist_id": artist_id,
                            "artist_name": artist_name
                        }
                    )
                    menu_nodes.append(node)
            
            logger.info(f"Created {len(menu_nodes)} artist nodes for range {start_letter}-{end_letter}")
            return menu_nodes
            
        except Exception as e:
            logger.error(f"Failed to create artists in range menu: {e}")
            return []

    def create_artist_albums_menu(self, artist_id: str) -> List[MenuNode]:
        """
        Create menu nodes for all albums by a specific artist.
        
        Args:
            artist_id: The Subsonic ID of the artist
            
        Returns:
            List of MenuNode objects for each album by the artist
        """
        try:
            albums = self.subsonic_service.list_albums_for_artist(artist_id)
            menu_nodes = []
            
            for album in albums:
                album_id = album.get("id")
                album_name = album.get("name")
                
                if album_id and album_name:
                    node = MenuNode(
                        id=f"album_{album_id}",
                        name=album_name,
                        payload={
                            "action": "play_album",
                            "album_id": album_id,
                            "album_name": album_name
                        }
                    )
                    menu_nodes.append(node)
            
            logger.info(f"Created {len(menu_nodes)} album nodes for artist {artist_id}")
            return menu_nodes
            
        except Exception as e:
            logger.error(f"Failed to create artist albums menu: {e}")
            return []

    def get_dynamic_menu_nodes(self, menu_type: str, **kwargs) -> List[MenuNode]:
        """
        Get dynamic menu nodes based on menu type and parameters.
        
        Args:
            menu_type: Type of menu to generate
            **kwargs: Additional parameters for menu generation
            
        Returns:
            List of MenuNode objects
        """
        if menu_type == "artists_alphabetical":
            return self.create_artists_alphabetical_menu()
        elif menu_type == "artists_in_range":
            return self.create_artists_in_range_menu(
                kwargs.get("start_letter"), 
                kwargs.get("end_letter")
            )
        elif menu_type == "artist_albums":
            return self.create_artist_albums_menu(kwargs.get("artist_id"))
        else:
            logger.warning(f"Unknown menu type: {menu_type}")
            return []
